"""Step 06 -- plan: cut the beat walk over the MEASURED metre, then fill it.

The cue's metre (step 03) owns every cut: whole beats, every L0 event, one
hold into the title.  Setups fill the cuts from the screenplay's own framings
and the gate is the one the old plan could not fail: a setup whose scene holds
a face with no reference sheet is refused, because the render would invent
that face.  The ladder substitutes another setup for the same cut, then makes
the shot an empty plate, and drops the beat as a last resort.  Lines, where
steps 04 and 05 have run, are windowed into the cue's measured slots.
"""
from __future__ import annotations

import json

from scripts.trailer.build_plan import beat_of, shots_for
from scripts.trailer.step_07_clips import RENDER_SECONDS
from studio.ladder import Ladder, Rung, climb
from studio.trailer_dialogue import dialogue_candidates, pick_lines
from studio.trailer_edit import LITERARY_STRETCH, plan_cuts
from studio.trailer_spec import MusicBed, RefSheet, TrailerBeat, TrailerPlan
from studio.trailer_stage_spec import LineSlate, Metre, SlateLine, StorySpec, VoiceLine
from studio.trailer_story import load_iconicity, select_setups

STEP_ID = "06"
NAME = "plan"
LEAD_SHARE_FLOOR = 0.25
RETRY_RESERVE = 1
"""Takes left unplanned so one identity reroll anywhere costs no beat: the
budget rung drops the LAST setups, and the last setups are the climax."""
STRETCH = (1.0, 1.2, 1.5)
"""Recut attempts lengthen the shots: fewer cuts need fewer clips, so fewer
neighbouring takes stand in for missing ones.  First setting."""
PLATE = "Empty plate, nobody in frame. "
TROUGH_GAP = 1.0


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


def setup_count(cuts: int, ctx) -> int:
    """One setup per cut, capped by the takes step 07's share still affords."""
    affordable = int(ctx.budget.remaining("07") // RENDER_SECONDS) - RETRY_RESERVE
    return max(1, min(cuts, affordable))


def setups_for(scenes: list[dict], refs, count: int, iconicity: dict,
               lead: str | None, figure: str | None) -> list[TrailerBeat]:
    elements = select_setups(scenes, set(refs), count, iconicity)
    return [beat_of(e, i, i / max(len(elements) - 1, 1), refs, lead, figure)
            for i, e in enumerate(elements)]


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


def alternates(scenes: list[dict], refs, used: set, iconicity: dict, count: int) -> list[dict]:
    """Setups whose every subject is sheeted, not yet in the plan, best first."""
    pool = select_setups(scenes, set(refs), 2 * (len(used) + count), iconicity)
    return [c for c in pool if (c["scene"], c["index"]) not in used
            and all(f"char-{p}" in refs for p in c["subjects"])][:count]


def substitute(beats: list[TrailerBeat], bad: list[str], spare: list[dict], refs,
               lead: str | None, figure: str | None) -> list[TrailerBeat]:
    """Another setup for the same cut, while spares last."""
    out = list(beats)
    for i, beat in enumerate(beats):
        if beat.beat_id in bad and spare:
            out[i] = beat_of(spare.pop(0), i, i / max(len(beats) - 1, 1), refs, lead, figure)
    return out


def plate(beats: list[TrailerBeat], bad: list[str]) -> list[TrailerBeat]:
    """The same place with nobody in it: the location sheet binds, faces do not."""
    return [b.model_copy(update={"cast": [], "subjects": [], "image_prompt": PLATE + b.image_prompt})
            if b.beat_id in bad else b for b in beats]


def ordered(slate: LineSlate, metre: Metre, figure: str, measured: dict,
            order=None) -> list[SlateLine]:
    """The slate re-ordered against the measured slots; slate order if the
    orderer (Track A's `order_lines`) is absent or refuses."""
    try:
        if order is None:
            from studio.trailer_dialogue import order_lines as order
        from studio.trailer_dialogue import windows_of
        beat = metre.beat if metre.grid == "metre" else None
        return order(slate.lines, windows_of(metre), figure, measured=measured, beat=beat,
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


def lines_for(ctx, metre: Metre, story: StorySpec, scenes: list[dict]) -> tuple[list[dict], list[dict]]:
    """(windows, legacy lines): voiced lines get windows and the shots carry
    no text; without a voice step the old on-shot dialogue placement stands."""
    slate_path, voice_path = ctx.out_dir / "lines.json", ctx.out_dir / "voice.json"
    if slate_path.exists() and voice_path.exists():
        slate = LineSlate.model_validate_json(slate_path.read_text(encoding="utf-8"))
        voiced = [VoiceLine.model_validate(v) for v in json.loads(voice_path.read_text(encoding="utf-8"))]
        measured = {v.text: v.seconds for v in voiced if v.seconds}
        return windows(ordered(slate, metre, story.figure, measured), slate.lines, metre), []
    candidates = dialogue_candidates(scenes, set(story.restricted_scenes), (story.lead, story.figure))
    return [], pick_lines(candidates, count=16, per_speaker=5)


def inputs(ctx) -> dict:
    book = ctx.book_dir
    refs_doc = json.loads((book / "refs/refs.json").read_text(encoding="utf-8"))
    return {"screenplay": json.loads((book / "screenplay/feature/screenplay.json").read_text(encoding="utf-8")),
            "refs_doc": refs_doc, "refs": {r["ref_id"]: r for r in refs_doc["refs"]},
            "story": StorySpec.model_validate_json((ctx.out_dir / "story.json").read_text(encoding="utf-8")),
            "metre": Metre.model_validate_json((ctx.out_dir / "music/metre.json").read_text(encoding="utf-8")),
            "iconicity": load_iconicity(book)}


def music_of(metre: Metre) -> MusicBed:
    before = [s for s in metre.stopdowns if metre.title_hit and s < metre.title_hit]
    return MusicBed(rel_path=metre.rel_path, seconds=metre.seconds, sections=9,
                    cuts=[b for b in metre.beats if b <= metre.seconds],
                    title_stopdown=before[-1] if before else None, title_impact=metre.title_hit)


def plan_for(found: dict, beats: list[TrailerBeat], points: list[float],
             legacy: list[dict], trailer_id: str) -> TrailerPlan:
    screenplay, refs = found["screenplay"], found["refs"]
    shots = shots_for(beats, points, screenplay, refs, legacy)
    return TrailerPlan(
        trailer_id=trailer_id, book_id=found["book_id"], title=screenplay["title"],
        refs=[RefSheet(ref_id=r["ref_id"], kind=r["kind"], name=r["name"],
                       prompt=r["prompt"], rel_path=r["rel_path"]) for r in found["refs_doc"]["refs"]],
        beats=beats, shots=shots, music=music_of(found["metre"]))


def verdict(state: dict) -> tuple[bool, str, str]:
    """Every setup sheeted and the lead in a quarter of the shots."""
    plan, bad = state["plan"], state["bad"]
    share = lead_share([s.cast for s in plan.shots], state["lead"])
    ok = not bad and share >= LEAD_SHARE_FLOOR
    return ok, f"{len(bad)} unbound, lead in {share:.0%}", f"0 unbound, lead >= {LEAD_SHARE_FLOOR:.0%}"


def write_plan(ctx, plan: TrailerPlan, windows: list[dict], stretch: float) -> None:
    """plan.json with the voice windows and the stretch beside the model."""
    doc = plan.model_dump(mode="json") | {"lines": windows, "stretch": stretch}
    ctx.out_dir.mkdir(parents=True, exist_ok=True)
    (ctx.out_dir / "plan.json").write_text(json.dumps(doc, indent=1), encoding="utf-8")
    print(f"[{STEP_ID}] {len(plan.beats)} setups, {len(plan.shots)} shots, "
          f"{len(windows)} line windows, stretch {stretch}")


LADDER = Ladder([Rung("select_setups", 0.0), Rung("alternate_setup_same_beat", 5.0),
                 Rung("location_only_shot", 5.0)], terminal="drop_beat")


def rung_beats(rung: Rung, state: dict, found: dict) -> list[TrailerBeat]:
    """The beats a rung proposes: the selection, substitutes, or plates."""
    beats, bad, story = state["beats"], state["bad"], found["story"]
    scenes = found["screenplay"]["scenes"]
    if rung.name == "alternate_setup_same_beat":
        used = {(b.scene_number, int(b.beat_id[1:])) for b in beats}
        spare = alternates(scenes, found["refs"], used, found["iconicity"], len(bad))
        return substitute(beats, bad, spare, found["refs"], story.lead, story.figure)
    if rung.name == "location_only_shot":
        return plate(beats, bad)
    return beats


def replan(ctx, attempt: int) -> None:
    """The whole plan at the stretch for `attempt`; step 08's recut calls this."""
    found = inputs(ctx) | {"book_id": ctx.book_dir.name}
    story, metre, scenes = found["story"], found["metre"], found["screenplay"]["scenes"]
    stretch = stretch_for(attempt)
    points = plan_cuts(metre, events_of(metre), metre.title_hit or metre.seconds, stretch)
    line_windows, legacy = lines_for(ctx, metre, story, scenes)
    state = {"beats": setups_for(scenes, found["refs"], setup_count(len(points) - 1, ctx),
                                 found["iconicity"],
                                 story.lead, story.figure), "bad": [], "lead": story.lead}

    def attempt_(rung, i):
        state["beats"] = rung_beats(rung, state, found)
        state["bad"] = unbound(state["beats"], found["refs"])
        state["plan"] = plan_for(found, state["beats"], points, legacy, ctx.trailer_id)
        return state

    if climb(LADDER, STEP_ID, attempt_, verdict, ctx.budget, ctx.learn, gate_name="binding").terminal:
        state["beats"] = [b for b in state["beats"] if b.beat_id not in state["bad"]]
        state["plan"] = plan_for(found, state["beats"], points, legacy, ctx.trailer_id)
    write_plan(ctx, state["plan"], line_windows, stretch)


def run(codex_id: str, ctx) -> None:
    replan(ctx, 0)
