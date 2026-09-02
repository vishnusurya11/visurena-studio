#!/usr/bin/env python
"""Build the trailer plan: which moment plays when, and what it is bound to.

The plan is refused if any shot shows a character it carries no reference for.
That gate is the whole lesson of the first trailer -- twelve good reference
sheets existed and the keyframe jobs were plain text-to-image, so nothing ever
told the model that Holmes looked like anything in particular.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio.trailer_edit import cut_points, lengths_of
from studio.trailer_plan import (action_featuring, arc_for, diversify_locations,
                                 leading_characters, quotable_lines,
                                 spread_lead)
from studio.trailer_spec import MusicBed, RefSheet, ShotSpec, TrailerBeat, TrailerPlan

ROOT = Path(__file__).resolve().parents[2]


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def beat_from_scene(scene: dict, index: int, position: float, refs: dict,
                    ranking: list[str], used: dict) -> TrailerBeat:
    """One trailer beat, traceable to one screenplay scene."""
    slug = scene["slug"]
    available = {r[len("char-"):] for r in refs if r.startswith("char-")}
    cast = spread_lead(scene, ranking, available, used)
    for who in cast:
        used[who] = used.get(who, 0) + 1
    lines = [l for l in quotable_lines(scene) if l["character"] in cast]
    chosen = lines[0] if lines else None
    names = [refs[f"char-{c}"]["name"] for c in cast if f"char-{c}" in refs]
    action = action_featuring(scene, names)
    return TrailerBeat(
        beat_id=f"B{index:02d}", scene_number=scene["number"], arc=arc_for(position),
        location_id=slug["location_id"], cast=cast,
        image_prompt=action or slug["text"],
        motion="The camera pushes in with small amplitude at slow speed.",
        line=chosen["text"] if chosen else None,
        speaker=chosen["character"] if chosen else None,
        emotion=(chosen.get("emotion") if chosen else None))


def shots_for(beats: list[TrailerBeat], points: list[float], refs: dict) -> list[ShotSpec]:
    """One shot per cut, cycling the beats so every beat gets screen time.

    Cycling is deliberate rather than lazy: a short repeated in-world action
    used as a rhythm anchor is a named prestige device (Woollen's chalkboard
    in A Serious Man, which Garrett calls the defining technique of the last
    decade), and it is the cheapest thing this pipeline can render.  What
    would be a defect -- reusing footage -- becomes the intention.
    """
    lengths = lengths_of(points)
    shots: list[ShotSpec] = []
    for index, (start, length) in enumerate(zip(points, lengths)):
        beat = beats[index % len(beats)]
        char_refs = {c: f"char-{c}" for c in beat.cast if f"char-{c}" in refs}
        loc_ref = f"loc-{beat.location_id}" if f"loc-{beat.location_id}" in refs else None
        shots.append(ShotSpec(beat_id=beat.beat_id, index=index, start=start,
                              seconds=length, cast=beat.cast,
                              char_refs=char_refs, loc_ref=loc_ref))
    return shots


def main(book_glob: str, trailer_id: str = "main") -> None:
    book = next(p for p in (ROOT / "library").iterdir() if p.name.startswith(book_glob))
    screenplay = load(book / "screenplay/feature/screenplay.json")
    refs_doc = load(book / "refs/refs.json")
    refs = {r["ref_id"]: r for r in refs_doc["refs"]}
    cues = load(book / "trailer/music/cues.json")
    cue = next(c for c in cues["candidates"] if c["seed"] == cues["chosen"])
    if not cue["title_impact"]:
        raise SystemExit("chosen cue has no title moment; regenerate the music")

    scenes = screenplay["scenes"]
    ranking = leading_characters(scenes)
    points = cut_points(cue["title_stopdown"], cue["grid"])
    # Only scenes whose LOCATION has a plate can be rendered at all -- a beat
    # with nothing to bind to is silently skipped downstream and then leaves a
    # hole in the cut.  Filter here, where it is visible.
    usable = [s for s in scenes
              if f"loc-{s.get('slug', {}).get('location_id')}" in refs]
    if len(usable) < 6:
        raise SystemExit(f"only {len(usable)} scenes have a location plate; "
                         "generate more refs before planning")
    picked = diversify_locations(usable, 11)
    # Position is the beat's place in the TRAILER, not in the screenplay.
    # Dividing by the scene count capped every beat at 0.48, so no beat ever
    # reached the "hit" band and the trailer had no climax.
    used: dict[str, int] = {}
    beats = [beat_from_scene(s, i, i / max(len(picked) - 1, 1), refs, ranking, used)
             for i, s in enumerate(picked)]
    shots = shots_for(beats, points, refs)

    plan = TrailerPlan(
        trailer_id=trailer_id, book_id=book.name, title=screenplay["title"],
        refs=[RefSheet(ref_id=r["ref_id"], kind=r["kind"], name=r["name"],
                       prompt=r["prompt"], rel_path=r["rel_path"])
              for r in refs_doc["refs"]],
        beats=beats, shots=shots,
        music=MusicBed(rel_path=cue["rel_path"], seconds=cue["seconds"],
                       sections=9, cuts=cue["grid"],
                       title_stopdown=cue["title_stopdown"],
                       title_impact=cue["title_impact"]))

    # A trailer must contain the story's lead.  Every mechanical gate passed a
    # Study in Scarlet plan that never once showed Sherlock Holmes, because
    # nothing was checking for him -- the checks only gate what they measure.
    lead = ranking[0] if ranking else None
    if lead and f"char-{lead}" in refs:
        appearances = sum(lead in beat.cast for beat in beats)
        if appearances < max(2, len(beats) // 4):
            raise SystemExit(
                f"REFUSED: {lead} leads this story but appears in only "
                f"{appearances} of {len(beats)} beats")
    # Every register of the arc must be represented, or there is no climax.
    missing = {"quiet", "build", "hit"} - {beat.arc for beat in beats}
    if missing:
        raise SystemExit(f"REFUSED: the trailer has no {sorted(missing)} beats; "
                         "it rises to nothing")

    unbound = plan.unbound_shots()
    if unbound:
        raise SystemExit(f"REFUSED: {len(unbound)} shots show a character with no "
                         f"reference: {sorted({c for s in unbound for c in s.unbound_cast()})}")

    out = book / "trailer" / trailer_id
    out.mkdir(parents=True, exist_ok=True)
    (out / "plan.json").write_text(plan.model_dump_json(indent=1), encoding="utf-8")
    print(f"{len(beats)} beats, {len(shots)} shots, all bound -> {out / 'plan.json'}")
    print(f"  title card at {cue['title_impact']}s, stopdown {cue['title_stopdown']}s, "
          f"cue {cue['seconds']}s")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "main")
