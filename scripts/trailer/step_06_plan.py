"""Step 06 -- plan: fit the beat walk to the TAKES, then fill every cut.

The render is the only fixed thing.  Step 07 costs ~16 min a take, so the
budget says how many takes exist, the walk gives up seconds until its cut
count fits them (`fit_points`), and the story authors exactly one setup per
cut.  One take, one shot: run 10 spread 25 takes over 51 shots and the owner
threw it out.

Inside that, the cue's metre (step 03) still owns every cut: whole beats,
every L0 event, one hold into the title.  The binding gate is the one the
old plan could not fail -- a setup whose frame holds a face with no reference
sheet is refused, because the render would invent that face.  The ladder
substitutes another setup for the same cut, then shoots the location alone,
and drops the beat as a last resort.  Lines, where steps 04 and 05 have run,
are windowed into the cue's measured slots, and a window past the end of the
picture is dropped with it.

The ORDER of those setups is the trailer's story spine: M1 world and hook, M2
problem and turn, M3 threat and climax, scene order inside each, and the
frames that answer the question held back to the last quarter
(`trailer_story.select_by_movement`).  `one_each` plays the beats in the order
it is handed them, so this list IS the trailer.  Every spoken line then lands
on the face that says it -- the picture moves inside its movement, never the
line (`speak_on_face`).  See docs/analysis/research/trailer-story-spine.md.
"""
from __future__ import annotations

import json
from collections import Counter

from scripts.trailer.build_plan import beat_of, shots_for
from scripts.trailer.step_07_clips import render_seconds_for
from studio.ladder import Ladder, Rung, climb
from studio.trailer_dialogue import dialogue_candidates, pick_lines
from studio.trailer_edit import LITERARY_STRETCH, plan_cuts
from studio.trailer_spec import MusicBed, RefSheet, TrailerBeat, TrailerPlan
from studio.trailer_stage_spec import LineSlate, Metre, SlateLine, StorySpec, VoiceLine
from studio.trailer_story import (MOVEMENTS, identity_scenes, load_iconicity, movement_bounds,
                                  movement_of, resolution_scenes, select_by_movement,
                                  select_setups)

STEP_ID = "06"
NAME = "plan"
LEAD_SHARE_FLOOR = 0.25
RETRY_RESERVE = 1
"""Takes left unplanned so one identity reroll anywhere costs no beat: the
budget rung drops the LAST setups, and the last setups are the climax."""
STRETCH = (1.0, 1.2, 1.5)
"""Recut attempts lengthen the shots.  With one take per shot the takes are
fixed, so a longer stretch buys a longer TRAILER out of the same renders."""
PLATE = "The room alone, the furniture and light holding the frame. "
"""What IS in the shot.  The old wording was a negation ("nobody in frame"),
and a negation is the one thing an image model cannot draw."""
TROUGH_GAP = 1.0
EPS = 0.05
"""A frame either side: how near the picture's end must come to the cue's
title hit before the card is allowed to be timed to it."""


def stretch_for(attempt: int) -> float:
    return LITERARY_STRETCH * STRETCH[min(attempt, len(STRETCH) - 1)]


def stopdown_starts(stopdowns: list[float], gap: float = TROUGH_GAP) -> list[float]:
    """One event per trough: `stopdowns` lists every quiet window in it."""
    starts: list[float] = []
    for when in sorted(stopdowns):
        if not starts or when - last > gap:
            starts.append(when)
        last = when
    return starts


def events_of(metre: Metre) -> list[float]:
    """The L0 events the walk must cut on: hits, trough starts, the title."""
    title = [metre.title_hit] if metre.title_hit else []
    return sorted(set(metre.hits) | set(stopdown_starts(metre.stopdowns)) | set(title))


def affordable_takes(ctx) -> int:
    """The takes step 07's remaining share can actually render.

    The render is the only fixed thing in the trailer: every other number --
    how many setups the story authors, how long the walk is, how long the
    trailer runs -- is derived from this one.  Run 10 inverted that, planned
    25 setups against a cycle it had guessed at 11 min, and the budget rung
    dropped the last six beats, which are the climax.  The cycle is the one
    this book's runs measured (`render_seconds_for`), the typed constant only
    until a run has written one.
    """
    return max(1, int(ctx.budget.remaining("07") // render_seconds_for(ctx)) - RETRY_RESERVE)


def fit_points(metre: Metre, events: list[float], takes: int,
               stretch: float = LITERARY_STRETCH) -> list[float]:
    """The longest walk whose cut count fits `takes`, half a bar at a time.

    A cut with no take of its own has to borrow one, and a borrowed take is
    a picture the viewer has already seen.  So the walk gives up seconds,
    never distinctness: the trailer is as long as the renders allow.
    """
    duration = metre.title_hit or metre.seconds
    while duration >= metre.bar:
        points = plan_cuts(metre, events, duration, stretch)
        if len(points) - 1 <= takes:
            return points
        duration -= metre.bar / 2
    raise ValueError(f"no walk fits {takes} takes")


def agree(metre: Metre, events: list[float], beats: list[TrailerBeat],
          stretch: float) -> tuple[list[TrailerBeat], list[float]]:
    """Beats and cuts made to match: the walk fitted, then the beats trimmed.

    Both directions are needed.  The walk shortens to the beats it has, and
    a walk that could not use them all hands the spares back.
    """
    points = fit_points(metre, events, len(beats), stretch)
    return beats[:len(points) - 1], points


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
                     locked: set[int]) -> int | None:
    """The nearest free beat of the SAME movement whose frame holds the
    speaker.  Same movement, because the movement is the story's order and
    a line is not worth breaking it for."""
    movement = beats[index].movement
    options = [i for i, b in enumerate(beats)
               if i not in locked and b.movement == movement and speaker in b.cast]
    return min(options, key=lambda i: abs(i - index)) if options else None


def speak_on_face(beats: list[TrailerBeat], points: list[float], laid: list[dict],
                  speakers: dict[int, str | None]) -> tuple[list[TrailerBeat], list[dict], list[dict]]:
    """Every spoken line over the face that speaks it (R3).

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
        other = face_in_movement(order, shot, speaker, locked | {shot})
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
            order=None, end: float | None = None) -> list[SlateLine]:
    """The slate re-ordered against the measured slots the picture reaches;
    slate order if the orderer (Track A's `order_lines`) is absent or refuses."""
    try:
        if order is None:
            from studio.trailer_dialogue import order_lines as order
        beat = metre.beat if metre.grid == "metre" else None
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


def lines_for(ctx, metre: Metre, story: StorySpec, scenes: list[dict],
              end: float | None = None) -> tuple[list[dict], list[dict], dict[int, str | None]]:
    """(windows, legacy lines, who speaks each window).

    Voiced lines get windows and the shots carry no text; without a voice
    step the old on-shot dialogue placement stands.  The speakers travel with
    the windows because a window that lands on the wrong face is not a
    placement, it is a voice with no mouth (`speak_on_face`).
    """
    slate_path, voice_path = ctx.out_dir / "lines.json", ctx.out_dir / "voice.json"
    if slate_path.exists() and voice_path.exists():
        slate = LineSlate.model_validate_json(slate_path.read_text(encoding="utf-8"))
        voiced = [VoiceLine.model_validate(v) for v in json.loads(voice_path.read_text(encoding="utf-8"))]
        measured = {v.text: v.seconds for v in voiced if v.seconds}
        laid = windows(ordered(slate, metre, story.figure, measured, end=end),
                       slate.lines, metre)
        return laid, [], {i: l.speaker for i, l in enumerate(slate.lines)}
    candidates = dialogue_candidates(scenes, set(story.restricted_scenes), (story.lead, story.figure))
    return [], pick_lines(candidates, count=16, per_speaker=5), {}


def inputs(ctx) -> dict:
    book = ctx.book_dir
    refs_doc = json.loads((book / "refs/refs.json").read_text(encoding="utf-8"))
    return {"screenplay": json.loads((book / "screenplay/feature/screenplay.json").read_text(encoding="utf-8")),
            "refs_doc": refs_doc, "refs": {r["ref_id"]: r for r in refs_doc["refs"]},
            "story": StorySpec.model_validate_json((ctx.out_dir / "story.json").read_text(encoding="utf-8")),
            "metre": Metre.model_validate_json((ctx.out_dir / "music/metre.json").read_text(encoding="utf-8")),
            "iconicity": load_iconicity(book)}


def music_of(metre: Metre, ends: float) -> MusicBed:
    """The bed, and the title moment ONLY when the picture reaches it.

    The card is held until the cue's hit.  A 25 s cut against a hit at 88 s
    therefore holds a static title for a minute -- so a picture that stops
    short takes its card on its own end instead.
    """
    hit = metre.title_hit if metre.title_hit and ends >= metre.title_hit - EPS else None
    before = [s for s in metre.stopdowns if hit and s < hit]
    return MusicBed(rel_path=metre.rel_path, seconds=metre.seconds, sections=9,
                    cuts=[b for b in metre.beats if b <= metre.seconds],
                    title_stopdown=before[-1] if before else None, title_impact=hit)


def plan_for(found: dict, beats: list[TrailerBeat], points: list[float],
             legacy: list[dict], trailer_id: str) -> TrailerPlan:
    screenplay, refs, story = found["screenplay"], found["refs"], found["story"]
    answers = identity_scenes(screenplay["scenes"], story.lead, story.figure)
    shots = shots_for(beats, points, screenplay, refs, legacy,
                      reveal={b.beat_id for b in beats if b.scene_number in answers})
    return TrailerPlan(
        trailer_id=trailer_id, book_id=found["book_id"], title=screenplay["title"],
        refs=[RefSheet(ref_id=r["ref_id"], kind=r["kind"], name=r["name"],
                       prompt=r["prompt"], rel_path=r["rel_path"]) for r in found["refs_doc"]["refs"]],
        beats=beats, shots=shots, music=music_of(found["metre"], points[-1]))


def verdict(state: dict) -> tuple[bool, str, str]:
    """Every setup sheeted and the lead in a quarter of the shots."""
    plan, bad = state["plan"], state["bad"]
    share = lead_share([s.cast for s in plan.shots], state["lead"])
    ok = not bad and share >= LEAD_SHARE_FLOOR
    return ok, f"{len(bad)} unbound, lead in {share:.0%}", f"0 unbound, lead >= {LEAD_SHARE_FLOOR:.0%}"


def write_plan(ctx, plan: TrailerPlan, windows: list[dict], stretch: float,
               refused: list[dict] | None = None) -> None:
    """plan.json with the voice windows, what was refused, and the stretch.

    A line that could not be laid on its speaker's face is recorded rather
    than dropped in silence: run 10 shipped one line over the wrong man and
    nothing on disk said so.
    """
    doc = plan.model_dump(mode="json") | {"lines": windows, "stretch": stretch,
                                          "lines_refused": refused or []}
    ctx.out_dir.mkdir(parents=True, exist_ok=True)
    (ctx.out_dir / "plan.json").write_text(json.dumps(doc, indent=1), encoding="utf-8")
    counted = Counter(b.movement for b in plan.beats)
    print(f"[{STEP_ID}] {len(plan.beats)} setups "
          f"({'/'.join(f'{m} {counted[m]}' for m in MOVEMENTS)}), {len(plan.shots)} shots, "
          f"{len(windows)} line windows, {len(refused or [])} refused, stretch {stretch}")


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


def replan(ctx, attempt: int) -> None:
    """The whole plan at the stretch for `attempt`; step 08's recut calls this.

    The order is the rule: takes first, then a walk that fits them, then one
    setup per cut.  Run 10 went the other way -- 44 cuts, then whatever the
    budget could render -- and 25 takes carried 51 shots.
    """
    found = inputs(ctx) | {"book_id": ctx.book_dir.name}
    story, metre, scenes = found["story"], found["metre"], found["screenplay"]["scenes"]
    stretch, events = stretch_for(attempt), events_of(metre)
    walk = fit_points(metre, events, affordable_takes(ctx), stretch)
    wanted = len(walk) - 1
    line_windows, legacy, speakers = lines_for(ctx, metre, story, scenes, walk[-1])
    beats, points = agree(metre, events, setups_for(scenes, found["refs"], wanted,
                                                    found["iconicity"], story.lead,
                                                    story.figure,
                                                    banned=story.restricted_scenes), stretch)
    state = {"beats": beats, "points": points, "bad": [], "lead": story.lead}

    def attempt_(rung, i):
        state["beats"] = rung_beats(rung, state, found)
        state["bad"] = unbound(state["beats"], found["refs"])
        state["plan"] = plan_for(found, state["beats"], state["points"], legacy, ctx.trailer_id)
        return state

    if climb(LADDER, STEP_ID, attempt_, verdict, ctx.budget, ctx.learn, gate_name="binding").terminal:
        kept = [b for b in state["beats"] if b.beat_id not in state["bad"]]
        state["beats"], state["points"] = agree(metre, events, kept, stretch)
        state["plan"] = plan_for(found, state["beats"], state["points"], legacy, ctx.trailer_id)
    laid, refused = lay(state, found, inside(line_windows, state["points"][-1]),
                        speakers, legacy, ctx.trailer_id)
    write_plan(ctx, state["plan"], laid, stretch, refused)


def lay(state: dict, found: dict, line_windows: list[dict],
        speakers: dict, legacy: list[dict], trailer_id: str) -> tuple[list[dict], list[dict]]:
    """Put the lines on their speakers' faces, re-cutting the plan if the
    picture had to be reordered to make room (R3)."""
    beats, laid, refused = speak_on_face(state["beats"], state["points"],
                                         line_windows, speakers)
    if [b.beat_id for b in beats] != [b.beat_id for b in state["beats"]]:
        state["beats"] = beats
        state["plan"] = plan_for(found, beats, state["points"], legacy, trailer_id)
    return laid, refused


def refit(ctx, attempt: int, rendered: list[str]) -> None:
    """Re-cut the plan around the takes that EXIST: fewer beats, shorter walk.

    Step 08's old answer to a missing clip was a neighbouring take, which is
    reuse wearing a different name -- 24% of run 10's picture.  A trailer
    that lost a take is a shorter trailer, and this is where it gets shorter.
    """
    found = inputs(ctx) | {"book_id": ctx.book_dir.name}
    plan = json.loads((ctx.out_dir / "plan.json").read_text(encoding="utf-8"))
    metre, stretch = found["metre"], stretch_for(attempt)
    have = set(rendered)
    beats, points = agree(metre, events_of(metre),
                          [TrailerBeat.model_validate(b) for b in plan["beats"]
                           if b["beat_id"] in have], stretch)
    line_windows, legacy, speakers = lines_for(ctx, metre, found["story"],
                                               found["screenplay"]["scenes"], points[-1])
    state = {"beats": beats, "points": points,
             "plan": plan_for(found, beats, points, legacy, ctx.trailer_id)}
    laid, refused = lay(state, found, inside(line_windows, points[-1]), speakers,
                        legacy, ctx.trailer_id)
    write_plan(ctx, state["plan"], laid, stretch, refused)


def run(codex_id: str, ctx) -> None:
    replan(ctx, 0)
