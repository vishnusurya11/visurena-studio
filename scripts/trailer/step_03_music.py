"""Step 03 -- music: render seeds, MEASURE each, rank on fitness, gate on the grid.

Eight seeds of one byte-identical caption ranged 0.31-0.97 bars-in-mode and
89-189 BPM against 84 asked, so the caption is a wish and the tracker is the
witness.  A batch of four is rendered, every seed gets a Metre, and the best
one passes only if it is above the fitness floor, on a metric grid, and has a
slot for a line.  The ladder changes the FORM (more seeds, then a new pulse
carrier in the same register) and never the register; the terminal rung ships
the best seed of all on its onset grid and says so, because a trailer without
music is worse than one cut to onsets.
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
FITNESS_FLOOR = 6.0
"""First setting.  The synthetic gate cue scores 12-17 with a slot and a title
hit and 1-3 without either; Scarlet's nine real seeds scored 0.3-2.5 on the
old formula because no seed had a trough long enough for a title.  Revisit at
the first retrospect with real measured seeds."""
BATCH = 4
RENDER_ESTIMATE = 240.0
"""Seconds per render until the first batch has been timed."""
CUE_SECONDS = 100.0


class CaptionSheet(BaseModel):
    """What a reauthor may change: the pulse carrier, never the register."""

    percussion: str = Field(min_length=10, description="what carries the pulse, struck on the beat")
    instruments: str = Field(min_length=10, description="secondary instruments, one holding the grid")
    bpm: int = Field(ge=60, le=160)


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


def best_of(metres: list[Metre]) -> Metre | None:
    return max(metres, key=lambda m: m.fitness) if metres else None


def verdict(best: Metre | None) -> tuple[bool, str, float]:
    """(passed, what was measured, floor): fitness, grid and a slot, all three."""
    if best is None:
        return False, "no seed rendered", FITNESS_FLOOR
    measured = f"fitness {best.fitness:.1f} {best.grid} {len(best.slots)} slots"
    ok = best.fitness >= FITNESS_FLOOR and best.grid == "metre" and bool(best.slots)
    return ok, measured, FITNESS_FLOOR


def reauthor_prompt(tone: Tone, best: Metre | None) -> str:
    heard = (f"The best seed so far measured {best.bpm:.0f} BPM with {best.bars_in_mode:.0%} "
             f"bars in mode and {len(best.slots)} quiet slots." if best else
             "No seed measured a steady bar; bars in mode were below the floor.")
    return (f"A film-trailer cue in this register: {tone.genre}. Lead: {tone.lead_instrument}. "
            f"Current pulse: {tone.percussion}. Secondary: {tone.instruments}. Asked {tone.bpm} BPM.\n"
            f"{heard}\nThe cut needs a grid a beat tracker can count in 4/4 bars, and one or two "
            f"quiet bars in the middle for a spoken line.\nKeep the register and the lead. Replace "
            f"the pulse carrier with instruments that are STRUCK on every beat and hold a steady "
            f"tempo, name a secondary instrument that holds the grid, and choose a bpm between 80 "
            f"and 140.")


def reauthor(tone: Tone, best: Metre | None) -> Tone:
    """One structured call: same register, new pulse carrier."""
    sheet = llm.structured(TIER, reauthor_prompt(tone, best), CaptionSheet)
    return replace(tone, percussion=sheet.percussion, instruments=sheet.instruments, bpm=sheet.bpm)


def ship(ctx, best: Metre | None) -> None:
    """Write the chosen Metre; an onset grid is shipped, but never silently."""
    if best is None:
        raise RuntimeError("step 03 rendered no cue; nothing to cut to")
    (ctx.out_dir / "music/metre.json").write_text(
        best.model_dump_json(indent=2, by_alias=True), encoding="utf-8")
    if best.grid == "onsets":
        ctx.tracker.log(f"seed {best.seed} shipped on the ONSET grid (rubato, "
                        f"{best.bars_in_mode:.0%} bars in mode)", level="WARNING", step_id=STEP_ID)
    print(f"[{STEP_ID}] seed {best.seed}: {best.bpm:.1f} bpm, {best.bars_in_mode:.0%} bars in "
          f"mode, {best.grid}, {len(best.slots)} slots, fitness {best.fitness:.1f}")


def ladder_for(render: float) -> Ladder:
    return Ladder([Rung("first_seeds", 0.0), Rung("four_more_seeds", BATCH * render),
                   Rung("reauthor_caption", BATCH * render, tries=2)], terminal="onset_grid")


def run(codex_id: str, ctx) -> None:
    state = {"tone": load_tone(ctx.book_dir), "render": RENDER_ESTIMATE,
             "timed": [], "found": [], "batches": 0}
    ladder = ladder_for(RENDER_ESTIMATE)

    def attempt(rung, i):
        if rung.name == "reauthor_caption":
            state["tone"] = reauthor(state["tone"], best_of(state["found"]))
        render_batch(ctx, caption(state["tone"]), seeds_for(state["batches"]), state)
        state["batches"] += 1
        for later in ladder.rungs[1:]:
            later.cost_seconds = BATCH * state["render"]
        return best_of(state["found"])

    climb(ladder, STEP_ID, attempt, verdict, ctx.budget, ctx.learn, gate_name="metre")
    ship(ctx, best_of(state["found"]))
