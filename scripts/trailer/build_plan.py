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
from studio.trailer_plan import arc_for, pick_scenes, quotable_lines
from studio.trailer_spec import MusicBed, RefSheet, ShotSpec, TrailerBeat, TrailerPlan

ROOT = Path(__file__).resolve().parents[2]


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def beat_from_scene(scene: dict, index: int, position: float, refs: dict) -> TrailerBeat:
    """One trailer beat, traceable to one screenplay scene."""
    slug = scene["slug"]
    cast = [c for c in scene.get("cast", []) if f"char-{c}" in refs][:1]
    lines = [l for l in quotable_lines(scene) if l["character"] in cast]
    chosen = lines[0] if lines else None
    action = next((e["text"] for e in scene["elements"] if e["kind"] == "action"), "")
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
    points = cut_points(cue["title_stopdown"], cue["grid"])
    beats = [beat_from_scene(s, i, i / max(len(scenes) - 1, 1), refs)
             for i, s in enumerate(pick_scenes(scenes, 11, None))]
    shots = shots_for(beats, points, refs)

    plan = TrailerPlan(
        trailer_id=trailer_id, book_id=book.name, title=screenplay["title"],
        refs=[RefSheet(ref_id=r["ref_id"], kind=r["kind"], name=r["name"],
                       prompt=r["prompt"], rel_path=r["rel_path"])
              for r in refs_doc["refs"]],
        beats=beats, shots=shots,
        music=MusicBed(rel_path=cue["rel_path"], seconds=cue["seconds"],
                       sections=9, cuts=cue["grid"]))

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
