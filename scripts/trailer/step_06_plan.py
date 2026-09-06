"""Step 06 -- plan: fill the cue's spans with story.

One path, one rule: nothing here invents a cut.  Step 03 wrote
music/plan.json, and the cue's MEASURED spans are the shot list -- one shot
per picture span, in and out on the span's own bounds, each kind filled by
its grammar (`studio.shot_grammar`: a section reveals on its downbeat, a
sustain carries one move and three timed actions, a phrase states one fact,
an accent is an insert with no face, a trough is a static answer).  The
frames the budget affords fold that plan by step 03's own rule
(`fit_to_frames`), never by inventing a shorter cut.  Without plan.json the
step refuses (`cue_plan_of`): there is no fallback that cuts a picture.
See docs/analysis/research/trailer-music-first.md.

The story authors exactly one setup per span.  One take, one shot: run 10
spread 25 takes over 51 shots and the owner threw it out.  The binding gate
is the one the old plan could not fail -- a setup whose frame holds a face
with no reference sheet is refused, because the render would invent that
face.  The ladder substitutes another setup for the same span, then shoots
the location alone, and drops the beat as a last resort.  Lines, where steps
04 and 05 have run, are windowed into the cue's own line windows, and a
window past the end of the picture is dropped with it.

The ORDER of those setups is the trailer's story spine: M1 world and hook, M2
problem and turn, M3 threat and climax, scene order inside each, and the
frames that answer the question held back to the last quarter
(`trailer_story.select_by_movement`).  The spans are filled in the order the
beats are handed over, so this list IS the trailer.  Every spoken line then
lands on the face that says it -- the picture moves inside its movement,
never the line (`speak_on_face`).  See docs/analysis/research/trailer-story-spine.md.

History: until BUILD row 55 this step carried "the beat walk" as a fallback,
a synthesised cut list fitted to the takes step 07 could afford.  Run 12
onward reads only the spans, so the walk is gone.
"""
from __future__ import annotations

import json
from collections import Counter

from scripts.trailer.build_plan import beat_of, hold_wide
from scripts.trailer.step_07_clips import read_seconds
from studio import frame_budget
from studio.cue_plan import CuePlan, CueSpan
from studio.cue_spans import ShorterCue, fit_to_budget, plan_fit
from studio.ladder import Ladder, Rung, climb
from studio.learnings import load
from studio.shot_grammar import FRAMING, INSERT, grammar_for, insert_text
from studio.trailer_plan import arc_of
from studio.trailer_spec import MusicBed, RefSheet, ShotSpec, TrailerBeat, TrailerPlan
from studio.trailer_stage_spec import LineSlate, Metre, SlateLine, StorySpec, VoiceLine
from studio.trailer_story import (MOVEMENTS, identity_scenes, load_iconicity, movement_bounds,
                                  movement_of, resolution_scenes, select_by_movement,
                                  select_setups)

STEP_ID = "06"
NAME = "plan"
LEAD_SHARE_FLOOR = 0.25
PLATE = "The room alone, the furniture and light holding the frame. "
"""What IS in the shot.  The old wording was a negation ("nobody in frame"),
and a negation is the one thing an image model cannot draw."""
EPS = 0.05
"""A frame either side: how near the picture's end must come to the cue's
title hit before the card is allowed to be timed to it."""


def inside(windows: list[dict], end: float) -> list[dict]:
    """The line windows the picture actually reaches; the rest are unheard."""
    return [w for w in windows if w["at"] < end]


def setups_for(scenes: list[dict], refs, count: int, iconicity: dict,
               lead: str | None, figure: str | None, banned=None) -> list[TrailerBeat]:
    """`count` beats in TRAILER order: world, then problem, then threat.

    `one_each` plays the beats in the order it is handed them, so this list
    IS the trailer's order.  Run 10 handed it a score ranking and let the
    scatterer space it out, which is how the killer's face arrived at 8.75 s
    and the handcuffs at 17 s.
    """
    banned = resolution_scenes(scenes, lead, figure) if banned is None else set(banned)
    bounds = movement_bounds(scenes, lead)
    elements = select_by_movement(scenes, set(refs), count, iconicity, lead, figure, banned)
    return [beat_of(e, i, i / max(len(elements) - 1, 1), refs, lead, figure,
                    movement=movement_of(e["scene"], bounds),
                    last=(i == len(elements) - 1))
            for i, e in enumerate(elements)]


def under(points: list[float], at: float) -> int | None:
    """The index of the shot playing at `at`, or None past the picture."""
    for index in range(len(points) - 1):
        if points[index] <= at < points[index + 1]:
            return index
    return None


def face_in_movement(beats: list[TrailerBeat], index: int, speaker: str,
                     locked: set[int] | frozenset[int]) -> int | None:
    """The nearest free beat of the SAME movement whose frame holds the
    speaker.  Same movement, because the movement is the story's order and
    a line is not worth breaking it for."""
    movement = beats[index].movement
    options = [i for i, b in enumerate(beats)
               if i not in locked and b.movement == movement and speaker in b.cast]
    return min(options, key=lambda i: abs(i - index)) if options else None


def speak_on_face(beats: list[TrailerBeat], points: list[float], laid: list[dict],
                  speakers: dict[int, str | None],
                  pinned: frozenset[int] | set[int] = frozenset()
                  ) -> tuple[list[TrailerBeat], list[dict], list[dict]]:
    """Every spoken line over the face that speaks it (R3).

    `pinned` slots never move: an accent's insert is an insert whoever is
    speaking, so a line that opens on one is refused rather than swapped.

    Run 10 laid Holmes's "You have been in Afghanistan" at 29.755 s over a
    shot of John Ferrier lowering Lucy onto the alkali plain, because
    `windows` placed lines by TIME and never asked the shot who was in it.

    The line does not move -- it was chosen for that window's music.  The
    PICTURE moves, inside its own movement, and a line whose speaker has no
    face in that movement is not laid at all and says why.
    """
    order, kept, refused, locked = list(beats), [], [], set()
    for window in sorted(laid, key=lambda w: w["at"]):
        shot = under(points, window["at"])
        speaker = speakers.get(window["index"])
        if shot is None:
            refused.append({**window, "why": "the picture ends before this window"})
            continue
        if not speaker or speaker in order[shot].cast:
            locked.add(shot)
            kept.append(window)
            continue
        if shot in pinned:
            refused.append({**window, "why": f"shot {shot} is an insert on an accent"})
            continue
        other = face_in_movement(order, shot, speaker, locked | pinned | {shot})
        if other is None:
            refused.append({**window, "why": f"no shot of {speaker} in {order[shot].movement}"})
            continue
        order[shot], order[other] = order[other], order[shot]
        locked.add(shot)
        kept.append(window)
    return order, kept, refused


def unbound(beats: list[TrailerBeat], refs) -> list[str]:
    """Beats whose frame holds a face with no sheet, unless shot as a plate.

    The frame, not the scene: a close-up of Hope in a scene that also holds
    an unsheeted Mormon is a shot of Hope, and Hope has a sheet.
    """
    return [b.beat_id for b in beats
            if any(f"char-{p}" not in refs for p in b.subjects)
            and not b.image_prompt.startswith(PLATE)]


def lead_share(casts: list[list[str]], lead: str | None) -> float:
    if not casts or not lead:
        return 0.0
    return sum(lead in cast for cast in casts) / len(casts)


def alternates(scenes: list[dict], refs, used: set, iconicity: dict, count: int,
               banned=()) -> list[dict]:
    """Setups whose every subject is sheeted, not yet in the plan, best first.

    A spare never comes from the resolution or from a scene that answers the
    trailer's question: a rescue is not a licence to show the ending.
    """
    banned = set(banned)
    pool = select_setups(scenes, set(refs), 4 * (len(used) + count), iconicity)
    return [c for c in pool if (c["scene"], c["index"]) not in used
            and c["scene"] not in banned
            and all(f"char-{p}" in refs for p in c["subjects"])][:2 * count or count]


def same_movement(spare: list[dict], movement: str, bounds: tuple[int, int]) -> dict | None:
    """The first spare that belongs to the movement whose slot is empty."""
    return next((c for c in spare if movement_of(c["scene"], bounds) == movement), None)


def substitute(beats: list[TrailerBeat], bad: list[str], spare: list[dict], refs,
               lead: str | None, figure: str | None,
               bounds: tuple[int, int] = (0, 0)) -> list[TrailerBeat]:
    """Another setup for the same cut, from the same movement while spares
    last.  The slot keeps its movement either way: the spine is the order,
    and a binding rescue may not reorder the story."""
    out = list(beats)
    for i, beat in enumerate(beats):
        if beat.beat_id not in bad or not spare:
            continue
        pick = same_movement(spare, beat.movement, bounds) or spare[0]
        spare.remove(pick)
        out[i] = beat_of(pick, i, i / max(len(beats) - 1, 1), refs, lead, figure,
                         movement=beat.movement, last=beat.arc == "aftermath")
    return out


def plate(beats: list[TrailerBeat], bad: list[str]) -> list[TrailerBeat]:
    """The same place with nobody in it: the location sheet binds, faces do not."""
    return [b.model_copy(update={"cast": [], "subjects": [], "image_prompt": PLATE + b.image_prompt})
            if b.beat_id in bad else b for b in beats]


def reachable(metre: Metre, end: float) -> list:
    """The windows the PICTURE reaches, or every window when it reaches none.

    Step 04 orders the slate against the cue, which runs as long as the music;
    step 06 cuts a picture as long as the takes the budget affords.  Spreading
    four lines across an 88 s cue and then showing 23 s of picture is how run
    10's successors would speak once and fall silent -- the windows past the
    end are not late, they do not exist.
    """
    from studio.trailer_dialogue import windows_of
    every = windows_of(metre)
    return [w for w in every if w.start < end] or every


def ordered(slate: LineSlate, metre: Metre, figure: str, measured: dict,
            order=None, end: float | None = None, slots=None) -> list[SlateLine]:
    """The slate re-ordered against the measured slots the picture reaches --
    the cue plan's own line windows when `slots` are handed in --
    slate order if the orderer (Track A's `order_lines`) is absent or refuses."""
    try:
        if order is None:
            from studio.trailer_dialogue import order_lines as order
        beat = metre.beat if metre.grid == "metre" else None
        if slots is None:
            slots = reachable(metre, end if end is not None else metre.seconds)
        return order(slate.lines, slots, figure, measured=measured, beat=beat,
                     iconicity=slate.iconicity).lines
    except (ImportError, ValueError) as why:
        print(f"[{STEP_ID}] slate order kept: {why}")
        return slate.lines


def windows(lines: list[SlateLine], slate_lines: list[SlateLine], metre: Metre) -> list[dict]:
    """Each spoken line at the window the orderer chose it for, entering a
    beat after it opens; a line placed nowhere is not laid."""
    by_text = {l.text: i for i, l in enumerate(slate_lines)}
    return [{"index": by_text[line.text], "at": round(line.window.start + metre.beat, 3)}
            for line in lines if not line.card and line.window is not None]


def lines_for(ctx, metre: Metre, story: StorySpec, end: float | None = None,
              slots=None) -> tuple[list[dict], dict[int, str | None]]:
    """(windows, who speaks each window); nothing without a voiced slate.

    Voiced lines get windows and the shots carry no text.  The speakers
    travel with the windows because a window that lands on the wrong face is
    not a placement, it is a voice with no mouth (`speak_on_face`).
    """
    slate_path, voice_path = ctx.out_dir / "lines.json", ctx.out_dir / "voice.json"
    if slate_path.exists() and voice_path.exists():
        slate = LineSlate.model_validate_json(slate_path.read_text(encoding="utf-8"))
        voiced = [VoiceLine.model_validate(v) for v in json.loads(voice_path.read_text(encoding="utf-8"))]
        measured = {v.text: v.seconds for v in voiced if v.seconds}
        laid = windows(ordered(slate, metre, story.figure, measured, end=end, slots=slots),
                       slate.lines, metre)
        return laid, {i: l.speaker for i, l in enumerate(slate.lines)}
    return [], {}


def inputs(ctx) -> dict:
    book = ctx.book_dir
    refs_doc = json.loads((book / "refs/refs.json").read_text(encoding="utf-8"))
    return {"screenplay": json.loads((book / "screenplay/feature/screenplay.json").read_text(encoding="utf-8")),
            "refs_doc": refs_doc, "refs": {r["ref_id"]: r for r in refs_doc["refs"]},
            "story": StorySpec.model_validate_json((ctx.out_dir / "story.json").read_text(encoding="utf-8")),
            "metre": Metre.model_validate_json((ctx.out_dir / "music/metre.json").read_text(encoding="utf-8")),
            "iconicity": load_iconicity(book)}


def title_of(cue: CuePlan, ends: float) -> tuple[float | None, float | None]:
    """(the trough the card rides in on, the hit) -- ONLY when the picture
    reaches the hit.

    The card is held until the cue's hit.  A 25 s cut against a hit at 88 s
    would hold a static title for a minute, so a picture that stops short
    takes its card on its own end instead.
    """
    hit = cue.title_hit if cue.title_hit and ends >= cue.title_hit - EPS else None
    troughs = [s.start for s in cue.spans if hit and s.kind == "trough" and s.start < hit]
    return (troughs[-1] if troughs else None), hit


def music_of(cue: CuePlan, spans: list[CueSpan]) -> MusicBed:
    """The bed as the plan records it: the cue's measured sections, the cuts
    on the starts of the spans the picture kept, the title where reached."""
    stopdown, hit = title_of(cue, spans[-1].end)
    return MusicBed(rel_path=cue.rel_path, seconds=cue.seconds, sections=cue.sections,
                    cuts=[s.start for s in spans], title_stopdown=stopdown, title_impact=hit)


def sheets_of(found: dict) -> list[RefSheet]:
    return [RefSheet(ref_id=r["ref_id"], kind=r["kind"], name=r["name"],
                     prompt=r["prompt"], rel_path=r["rel_path"]) for r in found["refs_doc"]["refs"]]


def answers_in(found: dict, beats: list[TrailerBeat]) -> set[str]:
    """The beats whose scene answers the trailer's question (R4 holds them wide)."""
    screenplay, story = found["screenplay"], found["story"]
    answers = identity_scenes(screenplay["scenes"], story.lead, story.figure)
    return {b.beat_id for b in beats if b.scene_number in answers}


def verdict(state: dict) -> tuple[bool, str, str]:
    """Every setup sheeted and the lead in a quarter of the shots."""
    plan, bad = state["plan"], state["bad"]
    share = lead_share([s.cast for s in plan.shots], state["lead"])
    ok = not bad and share >= LEAD_SHARE_FLOOR
    return ok, f"{len(bad)} unbound, lead in {share:.0%}", f"0 unbound, lead >= {LEAD_SHARE_FLOOR:.0%}"


def write_plan(ctx, plan: TrailerPlan, windows: list[dict], spans: list[CueSpan],
               refused: list[dict] | None = None) -> None:
    """plan.json with the voice windows, what was refused, and the cue's
    `spans` the shots were laid on ("path": "spans" -- the only path).

    A line that could not be laid on its speaker's face is recorded rather
    than dropped in silence: run 10 shipped one line over the wrong man and
    nothing on disk said so.
    """
    doc = plan.model_dump(mode="json") | {"lines": windows, "lines_refused": refused or [],
                                          "path": "spans",
                                          "spans": [s.model_dump(mode="json") for s in spans]}
    ctx.out_dir.mkdir(parents=True, exist_ok=True)
    (ctx.out_dir / "plan.json").write_text(json.dumps(doc, indent=1), encoding="utf-8")
    counted = Counter(b.movement for b in plan.beats)
    print(f"[{STEP_ID}] {len(plan.beats)} setups "
          f"({'/'.join(f'{m} {counted[m]}' for m in MOVEMENTS)}), {len(plan.shots)} shots, "
          f"{len(windows)} line windows, {len(refused or [])} refused, {len(spans)} spans")


LADDER = Ladder([Rung("select_setups", 0.0), Rung("alternate_setup_same_beat", 5.0),
                 Rung("location_only_shot", 5.0)], terminal="drop_beat")


def rung_beats(rung: Rung, state: dict, found: dict) -> list[TrailerBeat]:
    """The beats a rung proposes: the selection, substitutes, or plates."""
    beats, bad, story = state["beats"], state["bad"], found["story"]
    scenes = found["screenplay"]["scenes"]
    if rung.name == "alternate_setup_same_beat":
        used = {(b.scene_number, int(b.beat_id[1:])) for b in beats}
        banned = set(story.restricted_scenes) | identity_scenes(scenes, story.lead, story.figure)
        spare = alternates(scenes, found["refs"], used, found["iconicity"], len(bad), banned)
        return substitute(beats, bad, spare, found["refs"], story.lead, story.figure,
                          movement_bounds(scenes, story.lead))
    if rung.name == "location_only_shot":
        return plate(beats, bad)
    return beats


def replan(ctx) -> None:
    """The whole plan on the cue's spans; step 08's recut calls this."""
    found = inputs(ctx) | {"book_id": ctx.book_dir.name}
    plan = cue_plan_of(ctx)
    print(f"[{STEP_ID}] music/plan.json: {len(plan.picture_spans())} spans are the shot list")
    replan_spans(ctx, found, plan)


def refit(ctx, rendered: list[str]) -> None:
    """Re-cut the plan around the takes that EXIST: fewer beats, a folded cue.

    Step 08's old answer to a missing clip was a neighbouring take, which is
    reuse wearing a different name -- 24% of run 10's picture.  A trailer
    that lost a take is a shorter trailer, and this is where it gets shorter.
    """
    found = inputs(ctx) | {"book_id": ctx.book_dir.name}
    cue = cue_plan_of(ctx)
    plan = json.loads((ctx.out_dir / "plan.json").read_text(encoding="utf-8"))
    have = set(rendered)
    kept = [TrailerBeat.model_validate(b) for b in plan["beats"] if b["beat_id"] in have]
    refit_spans(ctx, found, cue, kept)


def run(codex_id: str, ctx) -> None:
    replan(ctx)


# --- the cue's spans ARE the shot list -----------------------------------------
#
# Nothing below cuts: step 03 measured the cue into spans, each span is one
# shot with the span's own in and out, and the only question left is how each
# KIND of span is filled -- which is the grammar's (`studio.shot_grammar`).


def cue_plan_of(ctx) -> CuePlan:
    """Step 03's measured spans.  Their absence is a refusal, never a
    fallback: no stage downstream may invent a cut."""
    path = ctx.out_dir / "music/plan.json"
    if not path.exists():
        raise FileNotFoundError(f"[{STEP_ID}] music/plan.json is missing: step 03 measures the "
                                f"cue into spans and step 06 has nothing else to cut on")
    return CuePlan.model_validate_json(path.read_text(encoding="utf-8"))


def cycle_of(ctx) -> frame_budget.Cycle:
    """The frames-to-seconds line this book's runs measured, typed until one has."""
    return frame_budget.Cycle.from_rows(load(ctx.learnings_path))


def picture_seconds_left(ctx, plan: CuePlan) -> float:
    """Step 07's remaining share once the reader session -- one sheet per
    span -- is paid for.  What is left renders the takes."""
    return max(0.0, ctx.budget.remaining("07") - read_seconds(len(plan.picture_spans())))


def fit_to_frames(plan: CuePlan, remaining_s: float, cycle: frame_budget.Cycle) -> CuePlan:
    """The plan folded a span at a time until its frames render inside the
    seconds left.  The fold is step 03's own (`plan_fit`: the latest accent
    first, then phrases merged; sections, sustains and troughs never move),
    so the shot list shrinks by the cue's rule and never by a cut of its own."""
    fitted = fit_to_budget(plan, remaining_s, cycle)
    if fitted is not plan:
        print(f"[{STEP_ID}] the frames afford {len(fitted.picture_spans())} of "
              f"{len(plan.picture_spans())} spans; the rest fold into their neighbours")
    return fitted


def counts_by_movement(plan: CuePlan) -> dict[str, int]:
    """How many shots each movement gets: read off the cue, never chosen."""
    grouped = plan.by_movement()
    return {m: len(grouped.get(m, [])) for m in MOVEMENTS}


def points_of(spans: list[CueSpan]) -> list[float]:
    """The cut points the spans already are: every start, then the last end."""
    return [s.start for s in spans] + [spans[-1].end]


def tail_of(plan: CuePlan, cut: CueSpan, index: int) -> CueSpan:
    """The card's span from `cut` onward: the picture stops on a bound the
    cue measured, and the tail takes the rest."""
    return CueSpan(index=index, start=cut.start, end=plan.seconds, kind="tail",
                   section=cut.section, movement=cut.movement,
                   bars=max((plan.seconds - cut.start) / plan.bar, 1e-3))


def ended_early(plan: CuePlan, count: int) -> CuePlan:
    """The plan's picture stopped after `count` spans, on the next span's
    own start.  Sections past that point leave with their spans."""
    picture = plan.picture_spans()
    cut = picture[count]
    spans = picture[:count] + [tail_of(plan, cut, count)]
    sections = [c for c in plan.sections if c.start < cut.start - 1e-6]
    return CuePlan.model_validate({**plan.model_dump(), "hard_out": cut.start,
                                   "sections": [c.model_dump() for c in sections],
                                   "spans": [s.model_dump() for s in spans]})


def folded_to(plan: CuePlan, count: int) -> CuePlan:
    """The plan at `count` picture spans, by the cue's own fold; when the
    spans that never move outnumber the takes, the picture ends early
    instead -- a trailer that lost a take is a shorter trailer."""
    try:
        return plan_fit(plan, count)
    except ShorterCue as why:
        print(f"[{STEP_ID}] {why}; the picture ends after {count} spans instead")
        return ended_early(plan, count)


def agree_spans(plan: CuePlan, beats: list[TrailerBeat]) -> tuple[list[TrailerBeat], CuePlan]:
    """Beats and spans made to match: the plan folded to the beats the story
    has, then the beats trimmed to the spans that survive."""
    if len(beats) < len(plan.picture_spans()):
        plan = folded_to(plan, len(beats))
    return beats[:len(plan.picture_spans())], plan


def restamped(beats: list[TrailerBeat], spans: list[CueSpan]) -> list[TrailerBeat]:
    """Each beat in the movement of the span it fills.  The cue's sections
    are the movement doors, and the arc follows the movement."""
    last = len(beats) - 1
    return [b.model_copy(update={"movement": s.movement, "arc": arc_of(s.movement, i == last)})
            for i, (b, s) in enumerate(zip(beats, spans))]


def insert_of(beat: TrailerBeat) -> TrailerBeat:
    """The beat as an insert: the object its action names, alone in frame,
    with nobody to bind."""
    if beat.image_prompt.startswith(INSERT):
        return beat
    return beat.model_copy(update={"cast": [], "subjects": [],
                                   "image_prompt": insert_text(beat.image_prompt)})


def inserts(beats: list[TrailerBeat], spans: list[CueSpan]) -> list[TrailerBeat]:
    """The beat under every accent made an insert; step 07 binds from the
    beat, so the face has to leave the BEAT, not only the shot."""
    return [insert_of(b) if s.kind == "accent" else b for b, s in zip(beats, spans)]


def spoken_in(span: CueSpan, laid: list[dict], speakers: dict) -> tuple[bool, str | None]:
    """Whether a laid line opens inside the span, and who says it."""
    for window in laid:
        if span.start <= window["at"] < span.end:
            return True, speakers.get(window["index"])
    return False, None


def refs_of(beat: TrailerBeat, refs) -> tuple[dict[str, str], str | None]:
    """The sheets the take binds: one per cast member that has one, the place."""
    char_refs = {c: f"char-{c}" for c in beat.cast if f"char-{c}" in refs}
    loc = f"loc-{beat.location_id}"
    return char_refs, loc if loc in refs else None


def sizes_for(beats: list[TrailerBeat], spans: list[CueSpan], reveal) -> list[str]:
    """The grammar's size per span, the answer held at BOUND_FLOOR (R4); an
    accent stays an insert whatever it shows."""
    sizes = [grammar_for(s, b.motion, b.image_prompt, b.cast).size for b, s in zip(beats, spans)]
    held = hold_wide(sizes, [b.beat_id for b in beats], [s.seconds for s in spans], reveal)
    return [g if s.kind == "accent" else h for g, h, s in zip(sizes, held, spans)]


def shot_from_span(index: int, beat: TrailerBeat, span: CueSpan, refs, size: str,
                   laid: list[dict], speakers: dict) -> ShotSpec:
    """One shot filling one span: in and out are the span's, the fill is
    its kind's grammar, the text stays on the voice track."""
    spoken, speaker = spoken_in(span, laid, speakers)
    grammar = grammar_for(span, beat.motion, beat.image_prompt, beat.cast, spoken, speaker)
    char_refs, loc_ref = refs_of(beat, refs)
    return ShotSpec(beat_id=beat.beat_id, index=index, start=span.start, seconds=span.seconds,
                    cast=beat.cast, char_refs=char_refs, loc_ref=loc_ref,
                    size=size, framing=FRAMING[size], span_kind=span.kind,
                    movement=span.movement, move=grammar.move, actions=grammar.actions,
                    speaker_mode=grammar.speaker_mode, reveal_at=grammar.reveal_at,
                    binds_face=bool(char_refs))


def shots_from_spans(beats: list[TrailerBeat], spans: list[CueSpan], refs,
                     laid: list[dict], speakers: dict, reveal=()) -> list[ShotSpec]:
    """One shot per picture span in the cue's order.  Nothing here chooses a
    length or a cut point; a count that differs was never fitted."""
    if len(beats) != len(spans):
        raise ValueError(f"{len(beats)} beats for {len(spans)} spans: fit them first "
                         f"(agree_spans)")
    sizes = sizes_for(beats, spans, reveal)
    return [shot_from_span(i, b, s, refs, size, laid, speakers)
            for i, (b, s, size) in enumerate(zip(beats, spans, sizes))]


def plan_from_spans(found: dict, beats: list[TrailerBeat], spans: list[CueSpan],
                    laid: list[dict], speakers: dict, trailer_id: str) -> TrailerPlan:
    shots = shots_from_spans(beats, spans, found["refs"], laid, speakers,
                             reveal=answers_in(found, beats))
    return TrailerPlan(
        trailer_id=trailer_id, book_id=found["book_id"], title=found["screenplay"]["title"],
        refs=sheets_of(found), beats=beats, shots=shots,
        music=music_of(found["cue"], spans))


def filled(beats: list[TrailerBeat], plan: CuePlan) -> tuple[list[TrailerBeat], list[CueSpan]]:
    """Beats fitted to the spans, stamped with their movements, the accents
    made inserts: the one shape every spans-path plan is built from."""
    beats, plan = agree_spans(plan, beats)
    spans = plan.picture_spans()
    return inserts(restamped(beats, spans), spans), spans


def pinned_of(spans: list[CueSpan]) -> frozenset[int]:
    """The slots no line may move a face into: the accents' inserts."""
    return frozenset(i for i, s in enumerate(spans) if s.kind == "accent")


def lay_spans(state: dict, found: dict, line_windows: list[dict], speakers: dict,
              trailer_id: str) -> tuple[list[dict], list[dict]]:
    """Lines on their speakers' faces (R3), then the shots built with the
    lines they carry: the grammar names how the face holds each one."""
    spans = state["spans"]
    beats, laid, refused = speak_on_face(state["beats"], points_of(spans), line_windows,
                                         speakers, pinned=pinned_of(spans))
    state["beats"] = inserts(restamped(beats, spans), spans)
    state["plan"] = plan_from_spans(found, state["beats"], spans, laid, speakers, trailer_id)
    return laid, refused


def opening_state(found: dict, cue: CuePlan) -> dict:
    """The ladder's first rung: one setup per picture span, in story order,
    fitted to the cue."""
    story, scenes = found["story"], found["screenplay"]["scenes"]
    beats = setups_for(scenes, found["refs"], len(cue.picture_spans()), found["iconicity"],
                       story.lead, story.figure, banned=story.restricted_scenes)
    state = {"bad": [], "lead": story.lead}
    state["beats"], state["spans"] = filled(beats, cue)
    return state


def replan_spans(ctx, found: dict, cue: CuePlan) -> None:
    """The cue folded to the frames, one setup per span, the binding ladder
    inside that, then the lines.  No cut is chosen here."""
    cue = fit_to_frames(cue, picture_seconds_left(ctx, cue), cycle_of(ctx))
    found["cue"] = cue
    line_windows, speakers = lines_for(ctx, found["metre"], found["story"], cue.hard_out,
                                       slots=cue.line_windows())
    state = opening_state(found, cue)

    def attempt_(rung, i):
        state["beats"], state["spans"] = filled(rung_beats(rung, state, found), cue)
        state["bad"] = unbound(state["beats"], found["refs"])
        state["plan"] = plan_from_spans(found, state["beats"], state["spans"], [], speakers,
                                        ctx.trailer_id)
        return state

    if climb(LADDER, STEP_ID, attempt_, verdict, ctx.budget, ctx.learn, gate_name="binding").terminal:
        kept = [b for b in state["beats"] if b.beat_id not in state["bad"]]
        state["beats"], state["spans"] = filled(kept, cue)
    laid, refused = lay_spans(state, found, inside(line_windows, state["spans"][-1].end),
                              speakers, ctx.trailer_id)
    write_plan(ctx, state["plan"], laid, state["spans"], refused)


def refit_spans(ctx, found: dict, cue: CuePlan, kept: list[TrailerBeat]) -> None:
    """The spans path around the takes that EXIST: the cue folds to the
    beats left, by its own rule.  A dropped take is a folded span; the
    settle of what the fold lengthens is step 08's."""
    found["cue"] = cue
    beats, spans = filled(kept, cue)
    line_windows, speakers = lines_for(ctx, found["metre"], found["story"], spans[-1].end,
                                       slots=cue.line_windows())
    state = {"beats": beats, "spans": spans}
    laid, refused = lay_spans(state, found, inside(line_windows, spans[-1].end), speakers,
                              ctx.trailer_id)
    print(f"[{STEP_ID}] refit: {len(kept)} takes exist, the cue folds to {len(spans)} spans")
    write_plan(ctx, state["plan"], laid, spans, refused)
