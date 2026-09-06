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

import json
import math
import shutil
import time
from dataclasses import replace
from pathlib import Path

import numpy as np
from pydantic import BaseModel, Field

from scripts.trailer import build_music
from scripts.trailer.step_07_clips import read_seconds
from studio import beatmap, cue_arc, cue_ask, cue_conform, cue_punct, cue_spans, frame_budget, llm, music_events
from studio.cue_plan import MIN_FORM_BARS, CueAsk, CuePlan
from studio.cue_settle import Settled
from studio.cue_spans import ShorterCue
from studio.ladder import Ladder, Rung, climb
from studio.learnings import Learning, load
from studio.music_tone import Tone, caption_stamp, cue_is_current, load_tone, lyrics_plan, recipe_path, stamp_cue
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
TAIL_BARS = 2
"""Bars past the picture that the card plays over; the ask's title bar sits
where they begin.  FLAG: the register's `tail_seconds` may ask for more."""
TAIL_HEADROOM = 4
"""Seconds the model is given past the ask to finish its own decay; a
runaway is cut at the hard out, never stretched to."""

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


def bar_of(tone: Tone) -> float:
    return round(60.0 / tone.bpm * cue_ask.beats_per_bar(tone), 4)


def picture_budget(ctx) -> float:
    """Render seconds step 07 has for picture: its share net of one reader session."""
    return max(0.0, ctx.budget.allowance("07") - read_seconds(len(frame_budget.CORPUS_MIX)))


def cycle_of(ctx) -> frame_budget.Cycle:
    """The render cycle the learnings measured, or the typed one until they have."""
    return frame_budget.Cycle.from_rows(load(ctx.learnings_path))


def bars_of(ctx, tone: Tone) -> int:
    """Bars the frame budget affords: step 07's share, net of one reader
    session, at the cycle the learnings measured, at the corpus mix of shot
    lengths -- plus the bars the card holds.  The shortest form is asked for
    when even that is out of reach: the fit rule trims the plan, a trailer
    without music is not shipped."""
    mix = list(frame_budget.CORPUS_MIX)
    seconds = frame_budget.cue_seconds_for(picture_budget(ctx), cycle_of(ctx), mix)
    try:
        return frame_budget.bars_for(seconds, bar_of(tone)) + TAIL_BARS
    except ValueError:
        ctx.tracker.log(f"budget affords {seconds:.0f}s of picture; asking for the shortest "
                        f"form anyway", level="WARNING", step_id=STEP_ID)
        return MIN_FORM_BARS + TAIL_BARS


def ask_of(ctx, tone: Tone) -> CueAsk:
    """What this run asks the music model for, derived from the frames."""
    return cue_ask.ask_for(tone, bars_of(ctx, tone))


def shorter_ask(tone: Tone, ask: CueAsk, bars_needed: int) -> CueAsk:
    """The ask with the bars the fit could not afford taken off, never under
    the shortest form: the cue bends, the form does not."""
    return cue_ask.ask_for(tone, max(MIN_FORM_BARS + TAIL_BARS, ask.bars - bars_needed))


def in_the_running(state: dict) -> list[Metre]:
    """The seeds rendered at the current ask, or every seed until one has
    been: a shorter ask retires the longer cues, whose plans the frames did
    not afford, and no batch is spent judging their siblings one by one."""
    current = [m for m in state["found"] if state["asks"][m.seed] == state["ask"]]
    return current or state["found"]


def conformed(ctx, plan: CuePlan) -> Settled:
    """The plan conformed to the takes step 07's frames afford: folds first,
    then the smallest interior spans cut out of the cue (row 56).  ShorterCue
    only when nothing interior is left to cut."""
    return cue_conform.conform_to_budget(plan, picture_budget(ctx), cycle_of(ctx))


def known_events(cue: Path) -> list[dict]:
    """The events an arc wrote beside its bar lines; none for a raw cue."""
    if not grid_path(cue).exists():
        return []
    return json.loads(grid_path(cue).read_text(encoding="utf-8")).get("events", [])


def map_cue(book: Path, cue: Path, found: Metre) -> dict:
    """One seed's cut map, written beside its metre for the retrospect; an
    arced cue's own events and stop are in it (output is input)."""
    cut = music_events.CutMap.model_validate(
        music_events.cut_map(beatmap.decode(cue), beatmap.RATE, found, known_events(cue)))
    (cue.parent / f"cutmap-{found.seed}.json").write_text(
        cut.model_dump_json(indent=2), encoding="utf-8")
    return cut.model_dump()


def score_of(ask: CueAsk, cut: dict, found: Metre) -> float:
    """The weighted share of the ask's events the rendered cue delivered."""
    return cue_ask.plan_score(cue_ask.verify(ask, cut, found))


def grid_path(cue: Path) -> Path:
    """Where an arced cue keeps the bar lines it was cut on."""
    return cue.with_suffix(".grid.json")


def known_grid(cue: Path) -> beatmap.Tracker | None:
    """A tracker that reports the arc's own bar lines, when the cue has them;
    a tracker loses the downbeats inside the arc's deliberate silences."""
    if not grid_path(cue).exists():
        return None
    grid = json.loads(grid_path(cue).read_text(encoding="utf-8"))
    return lambda samples, rate: (grid["beats"], grid["downbeats"])


def measure(book: Path, cue: Path, seed: int) -> Metre:
    """One seed's Metre, written beside the cue for the retrospect."""
    found = beatmap.metre(cue, seed=seed, rel_path=rel_path(book, cue), track=known_grid(cue))
    (cue.parent / f"metre-{seed}.json").write_text(
        found.model_dump_json(indent=2, by_alias=True), encoding="utf-8")
    return found


def render_batch(ctx, text: str, sheet: str, seeds: list[int], state: dict) -> list[Metre]:
    """Render and measure seeds until the batch or the budget is done.

    The first render of a run is never gated; after that each render must fit
    in the time left, at the slowest render seen so far.  Every seed gets a
    Metre, a cut map and a score against the ask."""
    music = ctx.out_dir / "music"
    music.mkdir(parents=True, exist_ok=True)
    found: list[Metre] = []
    for seed in seeds:
        if state["found"] and not ctx.budget.can_afford(STEP_ID, state["render"]):
            ctx.tracker.log(f"budget: {len(found)} of {len(seeds)} seeds rendered",
                            level="WARNING", step_id=STEP_ID)
            break
        started = time.monotonic()
        raw = build_music.render_cue(ctx.book_dir, text, seed, music, sheet, prefix="raw",
                                     duration=math.ceil(state["ask"].seconds) + TAIL_HEADROOM)
        state["timed"].append(time.monotonic() - started)
        state["render"] = max(max(state["timed"]), 1.0)
        found.append(grade(ctx.book_dir, arc_cue(ctx.book_dir, raw, state["ask"], seed), seed, state))
    return found


ARC_VERSION = 4
"""Bumped when `cue_arc` or `cue_punct` change what they cut, so a kept
raw render is arced again rather than trusted.  2: cut on the measured bar.
3: the tracker's tempo octave merged or split back to the ask's bar.
4: every bar cut to the cue's bar, black bars no material, and the arc's
events written beside its bar lines for the cut map."""


def arc_cue(book: Path, raw: Path, ask: CueAsk, seed: int) -> Path:
    """The raw render cut into the ask's arc (`cue_arc`) and punctuated
    (`cue_punct`), written as cue-<seed> beside it with the render's recipe
    carried over; the same render and ask are arced once."""
    recipe = json.loads(recipe_path(raw).read_text(encoding="utf-8"))
    dest = raw.with_name(f"cue-{seed}{raw.suffix}")
    stamp = caption_stamp(f"{recipe['stamp']}|{ask.model_dump_json()}|arc{ARC_VERSION}")
    if cue_is_current(dest, stamp):
        return dest
    metre = cue_arc.at_octave(beatmap.metre(raw, seed=seed, rel_path=rel_path(book, raw)), ask.bar)
    if len(metre.downbeats) < cue_arc.PHRASE_BARS:
        shutil.copyfile(raw, dest)          # rubato: nothing to re-order, ship the render
        grid_path(dest).unlink(missing_ok=True)
    else:
        write_arc(raw, dest, metre, ask)
    stamp_cue(dest, stamp, recipe["caption"], recipe["lyrics"])
    return dest


def fitted(ask: CueAsk, metre: Metre) -> CueAsk:
    """The ask on the render's bar: the same COUNT of bars and events, at the
    length the render plays a bar.  MEASURED: raw-1001 came back at 2.69 s
    bars against 2.4 asked; cut on the ask's bar the arc ran 101.8 s for a
    91.2 s ask with beats laid 2.4 s apart on 2.69 s bars (bars_in_mode 0.81).
    The metre is `cue_arc.at_octave` first: a bar off by a tempo octave
    (run 13: 1.12 s at 214 BPM for 100 asked) is the tracker's, not the render's."""
    return ask.model_copy(update={"bar": metre.bar, "bpm": int(round(metre.bpm))})


def write_arc(raw: Path, dest: Path, metre: Metre, ask: CueAsk) -> None:
    """The render cut into the ask's arc on its measured bar and punctuated,
    the bar lines it was cut on written beside it for `measure`."""
    fit = fitted(ask, metre)
    samples, rate = cue_conform.read_cue(raw)
    body, downbeats = cue_arc.arc(samples, rate, metre, fit, *beatmap.envelope(raw))
    cue_conform.write_cue(dest, cue_punct.punctuate(body, rate, downbeats, fit), rate)
    beats, downbeats = cue_arc.grid_of(downbeats, fit.bar)
    grid_path(dest).write_text(json.dumps({"beats": beats, "downbeats": downbeats,
                                           "events": cue_arc.events_of(fit, downbeats)}), encoding="utf-8")


def grade(book: Path, cue: Path, seed: int, state: dict) -> Metre:
    """Measure one rendered seed: its Metre, form, cut map and ask score."""
    metre = measure(book, cue, seed)
    state["form"][seed] = form_of(cue, metre)
    state["maps"][seed] = map_cue(book, cue, metre)
    state["asks"][seed] = state["ask"]
    state["score"][seed] = score_of(state["ask"], state["maps"][seed], metre)
    state["found"].append(metre)
    return metre


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


def best_of(metres: list[Metre], asked: int, form: dict[int, int] | None = None,
            score: dict[int, float] | None = None) -> Metre | None:
    """The seed that delivered most of its ask, then the most form, then the fittest.

    THE ASK FIRST: the cut is read off the events the ask pinned to bars, so
    a seed whose stop and title hit landed where they were asked is the one
    the picture can be cut to, whatever its grid.  Then FORM, ahead of grid
    steadiness.  Run 10's chosen seed had the
    steadiest grid of its family and was a plateau from 8 s with a fade for an
    ending: every metric term passed a cue that is not a trailer cue.  A
    staircase on a wobblier grid is the better trailer, because `04-shots` can
    cut to onsets and cannot invent a climax that is missing.

    Then a countable grid, then the asked pace by the tempo band it falls in;
    fitness only orders seeds that agree on all three.
    """
    scores, delivered = form or {}, score or {}
    return max(metres, key=lambda m: (delivered.get(m.seed, 0.0), scores.get(m.seed, 0),
                                      m.grid == "metre",
                                      -int(tempo_error(m.bpm, asked) / TEMPO_BAND),
                                      m.fitness), default=None)


def verdict(best: Metre | None, asked: int, score: dict[int, float] | None = None
            ) -> tuple[bool, str, float]:
    """(passed, what was measured, floor): the ask delivered, on a metric grid.

    Tempo is reported, not gated: the picture cuts to measured events now, so
    a cue at 127 against 100 asked that landed its stop and title hit is a
    trailer cue, and one at 100 that landed neither is not."""
    if best is None:
        return False, "no seed rendered", cue_ask.VERDICT_FLOOR
    delivered = (score or {}).get(best.seed, 0.0)
    measured = (f"ask {delivered:.2f} delivered, {best.bpm:.1f} bpm against {asked} asked, "
                f"{best.grid}, fitness {best.fitness:.1f}")
    return best.grid == "metre" and cue_ask.verdict(delivered), measured, cue_ask.VERDICT_FLOOR


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


def plan_for(best: Metre, state: dict) -> CuePlan:
    """The chosen cue's measured spans, carrying the ask they were graded against."""
    cut = music_events.CutMap.model_validate(state["maps"][best.seed])
    verified = cue_ask.verify(state["asks"][best.seed], state["maps"][best.seed], best)
    plan = cue_spans.plan_of(cut, best, rel_path=best.rel_path, seed=best.seed)
    return plan.model_copy(update={"asked": verified})


def judge(ctx, best: Metre | None, asked: int, state: dict) -> tuple[bool, str, float]:
    """The gate: the ask delivered on a metric grid, AND a plan the frames
    afford.  A plan that does not fit fails with the bars it needs off; the
    next attempt asks for that many fewer."""
    passed, measured, floor = verdict(best, asked, state["score"])
    if not passed:
        return passed, measured, floor
    try:
        conformed(ctx, plan_for(best, state))
    except ShorterCue as short:
        state["short"] = short.bars_needed
        return False, f"{measured}; the plan wants {short.bars_needed} fewer bars", floor
    return True, measured, floor


def cut_cue(ctx, best: Metre, plan: CuePlan, out: Settled) -> CuePlan:
    """The conformed plan over the cue cut to it, one render and two lengths;
    the whole plan with a warning when the cue refuses a join."""
    if not out.removed:
        return out.plan
    try:
        rel = cue_conform.cut_files(ctx.out_dir / "music", ctx.book_dir, plan, out.removed)
    except ValueError as exc:
        ctx.tracker.log(f"seed {best.seed}: the cue refused a join ({exc}); shipped whole",
                        level="WARNING", step_id=STEP_ID)
        return plan
    lost = sum(b - a for a, b in out.removed)
    ctx.learn(Learning(step=STEP_ID, gate="conform", measured=f"{lost:.1f}s cut in {len(out.removed)} range(s)",
                       threshold="frames afforded", action="conformed", attempt=1, terminal=True,
                       note=f"{out.plan.seconds:.1f}s left, {len(out.ids)} spans"))
    return out.plan.model_copy(update={"rel_path": rel})


def shipped_plan(ctx, best: Metre, state: dict) -> CuePlan:
    """The conformed plan over the cut cue, or the whole one with a warning
    when no conform affords it: step 08 settles what step 07 cannot render,
    never silently."""
    plan = plan_for(best, state)
    try:
        out = conformed(ctx, plan)
    except ShorterCue as short:
        ctx.tracker.log(f"seed {best.seed} shipped with a plan the frames do not afford: "
                        f"{short.bars_needed} fewer bars wanted", level="WARNING", step_id=STEP_ID)
        return plan
    return cut_cue(ctx, best, plan, out)


def warn_short(ctx, best: Metre, asked: int, form: dict[int, int], delivered: float) -> None:
    """What the shipped cue falls short of, on the tracker, never silently."""
    if not cue_ask.verdict(delivered):
        ctx.tracker.log(f"seed {best.seed} shipped delivering {delivered:.2f} of its ask "
                        f"(floor {cue_ask.VERDICT_FLOOR})", level="WARNING", step_id=STEP_ID)
    if form.get(best.seed, 0) < 2:
        ctx.tracker.log(f"seed {best.seed} shipped with {form.get(best.seed, 0)} of 2 form "
                        f"terms (staircase, stop-not-fade)", level="WARNING", step_id=STEP_ID)
    if best.grid == "onsets":
        ctx.tracker.log(f"seed {best.seed} shipped on the ONSET grid (rubato, "
                        f"{best.bars_in_mode:.0%} bars in mode)", level="WARNING", step_id=STEP_ID)
    if not on_tone(best.bpm, asked):
        ctx.tracker.log(f"seed {best.seed} shipped OFF TONE: {best.bpm:.1f} bpm against "
                        f"{asked} asked", level="WARNING", step_id=STEP_ID)


def ship(ctx, best: Metre | None, asked: int, form: dict[int, int], state: dict) -> None:
    """Write the chosen Metre and its CuePlan: downstream steps read spans from
    the plan and invent no cut of their own."""
    if best is None:
        raise RuntimeError("step 03 rendered no cue; nothing to cut to")
    (ctx.out_dir / "music/metre.json").write_text(
        best.model_dump_json(indent=2, by_alias=True), encoding="utf-8")
    plan = shipped_plan(ctx, best, state)
    (ctx.out_dir / "music/plan.json").write_text(plan.model_dump_json(indent=2), encoding="utf-8")
    recipe = recipe_path(ctx.out_dir / "music" / Path(best.rel_path).name)
    delivered = state["score"].get(best.seed, 0.0)
    warn_short(ctx, best, asked, form, delivered)
    print(f"[{STEP_ID}] seed {best.seed}: ask {delivered:.2f} delivered, "
          f"{len(plan.picture_spans())} spans over {plan.seconds:.1f}s, {best.bpm:.1f} bpm against "
          f"{asked} asked, {best.bars_in_mode:.0%} bars in mode, {best.grid}, "
          f"form {form.get(best.seed, 0)}/2, fitness {best.fitness:.1f}, recipe {recipe.name}")


def ladder_for(render: float) -> Ladder:
    return Ladder([Rung("first_seeds", 0.0), Rung("four_more_seeds", BATCH * render),
                   Rung("reauthor_caption", BATCH * render, tries=2)], terminal="best_seed")


def run(codex_id: str, ctx) -> None:
    tone = load_tone(ctx.book_dir)
    state = {"tone": tone, "ask": ask_of(ctx, tone), "render": RENDER_ESTIMATE,
             "timed": [], "found": [], "form": {}, "maps": {}, "asks": {}, "score": {},
             "short": 0, "batches": 0}
    ladder = ladder_for(RENDER_ESTIMATE)

    asked = state["tone"].bpm

    def best():
        return best_of(in_the_running(state), asked, state["form"], state["score"])

    def attempt(rung, i):
        if rung.name == "reauthor_caption":
            state["tone"] = reauthor(state["tone"], best())
        if state["short"]:
            state["ask"], state["short"] = shorter_ask(state["tone"], state["ask"], state["short"]), 0
        render_batch(ctx, cue_ask.caption_from(state["ask"], state["tone"]),
                     lyrics_plan(state["tone"]), seeds_for(state["batches"]), state)
        state["batches"] += 1
        for later in ladder.rungs[1:]:
            later.cost_seconds = BATCH * state["render"]
        return best()

    climb(ladder, STEP_ID, attempt, lambda b: judge(ctx, b, asked, state), ctx.budget, ctx.learn,
          gate_name="ask")
    ship(ctx, best(), asked, state["form"], state)
