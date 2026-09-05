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

import numpy as np
from pydantic import BaseModel, Field

from scripts.trailer import build_music
from studio import beatmap, llm
from studio.ladder import Ladder, Rung, climb
from studio.music_tone import Tone, caption, load_tone, lyrics_plan, recipe_path
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

STAIRCASE_DB = 4.0
"""How far the last third must sit above the first for the cue to be climbing.

MEASURED on the shipped cue: tenths 8-9 at -17.0/-14.6 against tenths 2-3 at
-19.2/-15.9 -- plus 1.6 dB, which is flat.  A trailer cue's last third is
audibly a different piece from its first."""
LOUDEST_BAND = (0.75, 0.92)
"""Where the loudest five seconds belong.  The shipped cue put them at 52%,
which is what "sounds like a song" measures as; `trailer_cut` wants its
shortest shots at 85-90% and there has to be something there to cut."""


class CaptionSheet(BaseModel):
    """What a reauthor may change: the pulse carriers and the supporting
    instruments, never the register or the tempo (the gate measures against
    the tone's bpm)."""

    pulse_carriers: list[str] = Field(
        min_length=2, description="the instruments that play the pulse, in order of entry")
    supporting_instruments: str = Field(
        min_length=10, description="the instruments under the lead, one of them holding the grid")


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


def render_batch(ctx, text: str, sheet: str, seeds: list[int], state: dict) -> list[Metre]:
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
        cue = build_music.render_cue(ctx.book_dir, text, seed, music, sheet)
        state["timed"].append(time.monotonic() - started)
        state["render"] = max(max(state["timed"]), 1.0)
        found.append(measure(ctx.book_dir, cue, seed))
        state["form"][seed] = form_of(cue, found[-1])
        state["found"].append(found[-1])
    return found


def tenth_medians(db) -> list[float]:
    """The median level of each tenth of the cue, quietest-first-tenth and all."""
    return [float(np.median(part)) for part in np.array_split(np.asarray(db), 10)]


def loudest_start(times, db, width: float = 5.0) -> float:
    """Where the loudest `width` seconds of the cue begin, as a share of it."""
    span = max(1, int(width / beatmap.WINDOW))
    means = np.convolve(np.asarray(db), np.ones(span) / span, mode="valid")
    return float(times[int(np.argmax(means))]) / float(times[-1])


def climbs(times, db) -> bool:
    """C's staircase term: the last third is louder, and its peak is late.

    The one term that would have failed the shipped cue while nearly every
    existing term passed it -- bars_in_mode 0.94, P95-P5 26.1 dB, one slot --
    which is how a plateau reached at 8 s came to be the best of its four
    seeds.
    """
    tenths = tenth_medians(db)
    rises = float(np.median(tenths[7:9])) >= float(np.median(tenths[1:3])) + STAIRCASE_DB
    return rises and LOUDEST_BAND[0] <= loudest_start(times, db) <= LOUDEST_BAND[1]


def stops_dead(times, db, title_hit: float | None, bar: float) -> bool:
    """C's stop-not-fade term: nothing new sounds after the title hit.

    The shipped cue fell monotonically over five seconds from 97.1 s.  A fade
    under the title card reads as a song ending; the form wants stop, silence,
    impact, decay.
    """
    if title_hit is None:
        return False
    after = title_hit + bar
    return not [t for t in beatmap.onsets(times, db) if t > after]


def form_of(cue: Path, found: Metre) -> int:
    """How many of the two form terms this seed satisfies, out of two."""
    times, db = beatmap.envelope(cue)
    return int(climbs(times, db)) + int(stops_dead(times, db, found.title_hit, found.bar))


def tempo_error(bpm: float, asked: int) -> float:
    """How far the measured pulse sits from the asked bpm, as a share of it."""
    return abs(bpm - asked) / asked


def on_tone(bpm: float, asked: int) -> bool:
    return tempo_error(bpm, asked) <= TEMPO_BAND


def best_of(metres: list[Metre], asked: int, form: dict[int, int] | None = None) -> Metre | None:
    """The seed that satisfies most of what the gate grades, then the fittest.

    FORM FIRST, ahead of grid steadiness.  Run 10's chosen seed had the
    steadiest grid of its family and was a plateau from 8 s with a fade for an
    ending: every metric term passed a cue that is not a trailer cue.  A
    staircase on a wobblier grid is the better trailer, because `04-shots` can
    cut to onsets and cannot invent a climax that is missing.

    Then a countable grid, then the asked pace by the tempo band it falls in;
    fitness only orders seeds that agree on all three.
    """
    scores = form or {}
    return max(metres, key=lambda m: (scores.get(m.seed, 0), m.grid == "metre",
                                      -int(tempo_error(m.bpm, asked) / TEMPO_BAND),
                                      m.fitness), default=None)


def verdict(best: Metre | None, asked: int) -> tuple[bool, str, float]:
    """(passed, what was measured, band): a metric grid on the asked tempo."""
    if best is None:
        return False, "no seed rendered", TEMPO_BAND
    measured = (f"{best.bpm:.1f} bpm against {asked} asked, {best.grid}, "
                f"fitness {best.fitness:.1f}")
    return best.grid == "metre" and on_tone(best.bpm, asked), measured, TEMPO_BAND


def reauthor_prompt(tone: Tone, best: Metre | None, refused: str = "") -> str:
    """Ask for a pulse the tracker can count, in the words a player would read.

    Run 10 asked for "instruments STRUCK on every beat ... not double it, not
    a triple subdivision" and got a click track back: a metronome satisfies
    every word of that sentence.  What the cue needs is a staircase whose beat
    stays countable, so the brief names the shape and the roster instead.
    """
    heard = (f"The best seed so far measured {best.bpm:.0f} BPM against {tone.bpm} asked, with "
             f"{best.bars_in_mode:.0%} bars in mode." if best else
             "Every seed so far measured a rubato grid; bars in mode were below the floor.")
    asked = (f"A film-trailer cue in this register: {tone.genre}. Lead: {tone.lead_instrument}. "
             f"Current pulse: {tone.percussion_palette}. Supporting: "
             f"{tone.supporting_instruments}. Asked around {tone.bpm} BPM.\n{heard}\n"
             f"The cut walks 4/4 bars at around {tone.bpm} BPM, so the beat stays countable at "
             f"that pace while the felt speed doubles by subdivision.\n"
             f"Keep the register, the lead and the tempo. Name the pulse carriers in order of "
             f"entry, at least one of them an instrument with a strong rhythmic prior "
             f"(pizzicato strings, a snare, a bass drum, a ticking clock, piano bass octaves), "
             f"each entering a later section than the one before and staying to the end; then "
             f"name the supporting instruments, one of them holding the grid through the final "
             f"third. Write every phrase as what plays.")
    return f"{asked}\nYour last answer was refused: {refused}. Name what plays." if refused else asked


def reauthor(tone: Tone, best: Metre | None, tries: int = 2) -> Tone:
    """One structured call: same register, same tempo, a new pulse carrier.

    The answer is validated as a Tone before it is used, so a rewrite naming
    an absence, or a pulse of struck objects the model cannot play in time, is
    refused and asked again -- and if it is refused twice, the tone the book
    authored stands.
    """
    refused = ""
    for _ in range(tries):
        sheet = llm.structured(TIER, reauthor_prompt(tone, best, refused), CaptionSheet)
        try:
            return replace(tone, pulse_carriers=tuple(sheet.pulse_carriers),
                           supporting_instruments=sheet.supporting_instruments)
        except ValueError as why:
            refused = str(why)
    return tone


def ship(ctx, best: Metre | None, asked: int, form: dict[int, int]) -> None:
    """Write the chosen Metre; an onset grid, an off-tone pace or a cue that
    is not a staircase is shipped, but never silently."""
    if best is None:
        raise RuntimeError("step 03 rendered no cue; nothing to cut to")
    (ctx.out_dir / "music/metre.json").write_text(
        best.model_dump_json(indent=2, by_alias=True), encoding="utf-8")
    recipe = recipe_path(ctx.out_dir / "music" / Path(best.rel_path).name)
    if form.get(best.seed, 0) < 2:
        ctx.tracker.log(f"seed {best.seed} shipped with {form.get(best.seed, 0)} of 2 form "
                        f"terms (staircase, stop-not-fade)", level="WARNING", step_id=STEP_ID)
    if best.grid == "onsets":
        ctx.tracker.log(f"seed {best.seed} shipped on the ONSET grid (rubato, "
                        f"{best.bars_in_mode:.0%} bars in mode)", level="WARNING", step_id=STEP_ID)
    if not on_tone(best.bpm, asked):
        ctx.tracker.log(f"seed {best.seed} shipped OFF TONE: {best.bpm:.1f} bpm against "
                        f"{asked} asked", level="WARNING", step_id=STEP_ID)
    print(f"[{STEP_ID}] seed {best.seed}: {best.bpm:.1f} bpm against {asked} asked, "
          f"{best.bars_in_mode:.0%} bars in mode, {best.grid}, {len(best.slots)} slots, "
          f"form {form.get(best.seed, 0)}/2, fitness {best.fitness:.1f}, "
          f"recipe {recipe.name}")


def ladder_for(render: float) -> Ladder:
    return Ladder([Rung("first_seeds", 0.0), Rung("four_more_seeds", BATCH * render),
                   Rung("reauthor_caption", BATCH * render, tries=2)], terminal="best_seed")


def run(codex_id: str, ctx) -> None:
    state = {"tone": load_tone(ctx.book_dir), "render": RENDER_ESTIMATE,
             "timed": [], "found": [], "form": {}, "batches": 0}
    ladder = ladder_for(RENDER_ESTIMATE)

    asked = state["tone"].bpm

    def attempt(rung, i):
        if rung.name == "reauthor_caption":
            state["tone"] = reauthor(state["tone"], best_of(state["found"], asked, state["form"]))
        render_batch(ctx, caption(state["tone"]), lyrics_plan(state["tone"]),
                     seeds_for(state["batches"]), state)
        state["batches"] += 1
        for later in ladder.rungs[1:]:
            later.cost_seconds = BATCH * state["render"]
        return best_of(state["found"], asked, state["form"])

    climb(ladder, STEP_ID, attempt, lambda best: verdict(best, asked), ctx.budget, ctx.learn,
          gate_name="metre")
    ship(ctx, best_of(state["found"], asked, state["form"]), asked, state["form"])
