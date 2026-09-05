"""Step 03 -- music: render seeds, MEASURE each, gate on the grid at the asked pace.

Eight seeds of one byte-identical caption ranged 0.31-0.97 bars-in-mode and
89-189 BPM against 84 asked, so the caption is a wish and the tracker is the
witness.  A batch of four is rendered, every seed gets a Metre, and the best
one passes only if it is on a metric grid within a tempo mark of the bpm the
tone asked: the cut follows the measured pulse at face value, and run 9's
177.8 BPM in three against 84 asked was heard as 'random music, not the tone'.
The ladder changes the FORM (more seeds, then a new pulse carrier in the same
register at the same tempo) and never the register; the terminal rung ships
the best seed of all and says what is off about it, because a trailer without
music is worse than one cut to the wrong pace.
"""
from __future__ import annotations

import time
from dataclasses import replace
from pathlib import Path

from pydantic import BaseModel, Field

from scripts.trailer import build_music
from studio import beatmap, llm
from studio.ladder import Ladder, Rung, climb
from studio.music_tone import Tone, caption, load_tone
from studio.trailer_stage_spec import Metre

STEP_ID = "03"
NAME = "music"
TIER = "reasoning"
TEMPO_BAND = 0.15
"""How far the measured pulse may sit from the asked bpm, as a share of it:
one tempo mark (andante 76-108 is +-17% about 92).  Fitness had a floor of
6.0 that no real seed met (run 9's best 4.4, earlier 0.3-2.5); it orders
seeds within a band now and gates nothing.  A slot is no longer graded:
04-lines MAKES a window from any metric grid and the mix ducks under it."""
BATCH = 4
RENDER_ESTIMATE = 240.0
"""Seconds per render until the first batch has been timed."""
CUE_SECONDS = 100.0


class CaptionSheet(BaseModel):
    """What a reauthor may change: the pulse carrier, never the register or
    the tempo (the gate measures against the tone's bpm)."""

    percussion: str = Field(min_length=10, description="what carries the pulse, struck on the beat")
    instruments: str = Field(min_length=10, description="secondary instruments, one holding the grid")


def seeds_for(batch: int) -> list[int]:
    """Deterministic and disjoint per batch, so a re-run reuses its renders."""
    return [(batch + 1) * 1000 + i + 1 for i in range(BATCH)]


def rel_path(book: Path, path: Path) -> str:
    return path.relative_to(book).as_posix()


def measure(book: Path, cue: Path, seed: int) -> Metre:
    """One seed's Metre, written beside the cue for the retrospect."""
    found = beatmap.metre(cue, seed=seed, rel_path=rel_path(book, cue))
    (cue.parent / f"metre-{seed}.json").write_text(
        found.model_dump_json(indent=2, by_alias=True), encoding="utf-8")
    return found


def render_batch(ctx, text: str, seeds: list[int], state: dict) -> list[Metre]:
    """Render and measure seeds until the batch or the budget is done.

    The first render of a run is never gated; after that each render must fit
    in the time left, at the slowest render seen so far."""
    music = ctx.out_dir / "music"
    music.mkdir(parents=True, exist_ok=True)
    found: list[Metre] = []
    for seed in seeds:
        if state["found"] and not ctx.budget.can_afford(STEP_ID, state["render"]):
            ctx.tracker.log(f"budget: {len(found)} of {len(seeds)} seeds rendered",
                            level="WARNING", step_id=STEP_ID)
            break
        started = time.monotonic()
        cue = build_music.render_cue(ctx.book_dir, text, seed, music, CUE_SECONDS)
        state["timed"].append(time.monotonic() - started)
        state["render"] = max(max(state["timed"]), 1.0)
        found.append(measure(ctx.book_dir, cue, seed))
        state["found"].append(found[-1])
    return found


def tempo_error(bpm: float, asked: int) -> float:
    """How far the measured pulse sits from the asked bpm, as a share of it."""
    return abs(bpm - asked) / asked


def on_tone(bpm: float, asked: int) -> bool:
    return tempo_error(bpm, asked) <= TEMPO_BAND


def best_of(metres: list[Metre], asked: int) -> Metre | None:
    """The seed that satisfies most of what the gate grades, then the fittest.

    Fitness alone shipped Scarlet run 7 on a rubato seed (9.2, all of it
    dynamic range) over nine metric ones, and the cut put 0% of its cuts on
    a downbeat; a slot ahead of tempo shipped run 9 at 177.8 BPM against 84.
    The cut needs a countable grid first and the asked pace second, by the
    tempo band it falls in; fitness only orders seeds that agree on those."""
    return max(metres, key=lambda m: (m.grid == "metre", -int(tempo_error(m.bpm, asked) / TEMPO_BAND),
                                      m.fitness), default=None)


def verdict(best: Metre | None, asked: int) -> tuple[bool, str, float]:
    """(passed, what was measured, band): a metric grid on the asked tempo."""
    if best is None:
        return False, "no seed rendered", TEMPO_BAND
    measured = (f"{best.bpm:.1f} bpm against {asked} asked, {best.grid}, "
                f"fitness {best.fitness:.1f}")
    return best.grid == "metre" and on_tone(best.bpm, asked), measured, TEMPO_BAND


def reauthor_prompt(tone: Tone, best: Metre | None) -> str:
    heard = (f"The best seed so far measured {best.bpm:.0f} BPM against {tone.bpm} asked, with "
             f"{best.bars_in_mode:.0%} bars in mode." if best else
             "No seed measured a steady bar; bars in mode were below the floor.")
    return (f"A film-trailer cue in this register: {tone.genre}. Lead: {tone.lead_instrument}. "
            f"Current pulse: {tone.percussion}. Secondary: {tone.instruments}. Asked {tone.bpm} BPM.\n"
            f"{heard}\nThe cut needs a grid a beat tracker can count in 4/4 bars at {tone.bpm} BPM: "
            f"not double it, not a triple subdivision.\nKeep the register, the lead and the tempo. "
            f"Replace the pulse carrier with instruments that are STRUCK on every beat and hold "
            f"{tone.bpm} BPM from first bar to last, and name a secondary instrument that holds "
            f"the grid.")


def reauthor(tone: Tone, best: Metre | None) -> Tone:
    """One structured call: same register, same tempo, new pulse carrier."""
    sheet = llm.structured(TIER, reauthor_prompt(tone, best), CaptionSheet)
    return replace(tone, percussion=sheet.percussion, instruments=sheet.instruments)


def ship(ctx, best: Metre | None, asked: int) -> None:
    """Write the chosen Metre; an onset grid or an off-tone pace is shipped,
    but never silently."""
    if best is None:
        raise RuntimeError("step 03 rendered no cue; nothing to cut to")
    (ctx.out_dir / "music/metre.json").write_text(
        best.model_dump_json(indent=2, by_alias=True), encoding="utf-8")
    if best.grid == "onsets":
        ctx.tracker.log(f"seed {best.seed} shipped on the ONSET grid (rubato, "
                        f"{best.bars_in_mode:.0%} bars in mode)", level="WARNING", step_id=STEP_ID)
    if not on_tone(best.bpm, asked):
        ctx.tracker.log(f"seed {best.seed} shipped OFF TONE: {best.bpm:.1f} bpm against "
                        f"{asked} asked", level="WARNING", step_id=STEP_ID)
    print(f"[{STEP_ID}] seed {best.seed}: {best.bpm:.1f} bpm against {asked} asked, "
          f"{best.bars_in_mode:.0%} bars in mode, {best.grid}, {len(best.slots)} slots, "
          f"fitness {best.fitness:.1f}")


def ladder_for(render: float) -> Ladder:
    return Ladder([Rung("first_seeds", 0.0), Rung("four_more_seeds", BATCH * render),
                   Rung("reauthor_caption", BATCH * render, tries=2)], terminal="best_seed")


def run(codex_id: str, ctx) -> None:
    state = {"tone": load_tone(ctx.book_dir), "render": RENDER_ESTIMATE,
             "timed": [], "found": [], "batches": 0}
    ladder = ladder_for(RENDER_ESTIMATE)

    asked = state["tone"].bpm

    def attempt(rung, i):
        if rung.name == "reauthor_caption":
            state["tone"] = reauthor(state["tone"], best_of(state["found"], asked))
        render_batch(ctx, caption(state["tone"]), seeds_for(state["batches"]), state)
        state["batches"] += 1
        for later in ladder.rungs[1:]:
            later.cost_seconds = BATCH * state["render"]
        return best_of(state["found"], asked)

    climb(ladder, STEP_ID, attempt, lambda best: verdict(best, asked), ctx.budget, ctx.learn,
          gate_name="metre")
    ship(ctx, best_of(state["found"], asked), asked)
