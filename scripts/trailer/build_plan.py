#!/usr/bin/env python
"""Build the trailer plan: which image plays when, and what it is bound to.

Selection happens at the ELEMENT level.  A scene is ninety seconds of story and
a trailer shot is two, so choosing scenes gave eleven candidates for thirty-three
shots and every setup appeared three times -- in strict rotation, the same
sequence over and over, which is why the first cuts read as loops.

This script previously imported none of that: `studio/trailer_story.py` existed,
was tested, was documented as the fix, and was dead code with respect to the
thing that actually shipped.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio.shot_grammar import (FRAMING, cause_of, choose_sizes,
                                 destination_of, motivated_move)
from studio.trailer_dialogue import assign_lines, dialogue_candidates, pick_lines
from studio.trailer_edit import cut_points, lengths_of
from studio.trailer_order import best_scatter, refuse_repetitive
from studio.trailer_plan import arc_for
from studio.trailer_spec import MusicBed, RefSheet, ShotSpec, TrailerBeat, TrailerPlan
from studio.trailer_story import (action_text, figure_of, lead_of,
                                  load_iconicity, people_in, principal_of,
                                  resolution_scenes, select_setups, turn_of)

ROOT = Path(__file__).resolve().parents[2]
SETUPS = 18


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def beat_of(element: dict, index: int, position: float, refs: dict,
            lead: str | None, figure: str | None) -> TrailerBeat:
    """One beat from one action line, cast from WHO IS IN THAT SCENE.

    The camera sentence is derived from this beat's own action line, so a beat
    that names nothing photographable gets a locked-off frame rather than the
    twenty-third copy of the same slow push-in.
    """
    principal = principal_of(element["cast"], set(refs), lead, figure)
    # The setup's OWN camera term drives the move.  Passing a constant "medium"
    # here made camera_for return "tracks in" for all nine beats, so every take
    # was the same push-in -- and a push-in sampled at four offsets is one image
    # at four focal lengths, which is why 23% of the cut was duplicate frames.
    return TrailerBeat(
        beat_id=f"B{index:02d}", scene_number=element["scene"], arc=arc_for(position),
        location_id=element["location_id"], cast=[principal] if principal else [],
        image_prompt=action_text(element),
        motion=move_for(element, position))


TERM_MOVE = {"dolly in": ("pushes in", "small"), "handheld": ("follows", "moderate"),
             "rack focus": ("racks focus", "small"), "pan left": ("pans left", "wide"),
             "pan right": ("pans right", "wide"), "tilt up": ("tilts up", "wide"),
             "locked-off": ("static", "")}
"""The screenplay already chose the move; honour it rather than inventing one."""


def move_for(setup: dict, position: float) -> str:
    """This setup's own camera sentence, from the term the adapter wrote."""
    move, amplitude = TERM_MOVE.get(setup.get("term", "locked-off"),
                                    ("pushes in", "small"))
    if move == "static":
        return motivated_move("static", "", "", "", "")
    text = action_text(setup)
    destination = destination_of(text) or "the subject"
    return motivated_move(move, amplitude, "quick" if position >= 0.85 else "slow",
                          cause_of(text), destination)


def shots_for(beats: list[TrailerBeat], points: list[float], scenes: dict,
              refs: dict, lines: list[dict]) -> list[ShotSpec]:
    """Assign beats to cut points WITHOUT repeating the beat sequence.

    The previous rule was `beats[index % len(beats)]`, which produced B00..B10
    three times over -- not scattered reuse but the same sequence played three
    times, each pass faster.  That is a loop, and no gate looked for one.
    """
    lengths = lengths_of(points)
    order = best_scatter([b.beat_id for b in beats], len(lengths))
    try:
        refuse_repetitive(order, min_gap=3, max_repeat=3)
    except ValueError as why:
        raise SystemExit(f"REFUSED: {why}") from why
    by_id = {b.beat_id: b for b in beats}

    bound = [bool(by_id[i].cast) for i in order]
    spots = [i / max(len(order) - 1, 1) for i in range(len(order))]
    sizes = choose_sizes(lengths, bound, spots)

    # Dialogue is placed against the SHOTS, because only a shot knows how long
    # it lasts, and a line that outlasts its picture is cut off mid-word.
    slots = [{"beat_id": f"{b}#{i}", "scene": by_id[b].scene_number,
              "cast": by_id[b].cast, "seconds": s}
             for i, (b, s) in enumerate(zip(order, lengths))]
    spoken = assign_lines(slots, lines)

    shots: list[ShotSpec] = []
    for index, (start, length, beat_id) in enumerate(zip(points, lengths, order)):
        beat = by_id[beat_id]
        char_refs = {c: f"char-{c}" for c in beat.cast if f"char-{c}" in refs}
        loc_ref = f"loc-{beat.location_id}" if f"loc-{beat.location_id}" in refs else None
        said = spoken.get(f"{beat_id}#{index}")
        shots.append(ShotSpec(beat_id=beat_id, index=index, start=start,
                              seconds=length, cast=beat.cast,
                              char_refs=char_refs, loc_ref=loc_ref,
                              size=sizes[index], framing=FRAMING[sizes[index]],
                              line=said["text"] if said else None,
                              speaker=said["speaker"] if said else None,
                              line_span=said["span"] if said else 1))
    return shots


def refuse_unbindable(beats: list[TrailerBeat], scenes: list[dict],
                      refs: dict) -> None:
    """Check binding against the SCENE's real cast, not the filtered one.

    The old gate could not fail.  `cast` was filtered to characters that have a
    reference BEFORE `char_refs` was built from it, so coverage was guaranteed
    by construction -- and Jekyll shipped four shots with no character at all
    while every gate reported "every shot carries its characters' references".
    Asking what the SOURCE scene contains is a question the plan cannot answer
    by construction.
    """
    by_number = {s["number"]: s for s in scenes}
    naked = [b.beat_id for b in beats if not b.cast]
    if len(naked) > len(beats) // 3:
        raise SystemExit(f"REFUSED: {len(naked)} of {len(beats)} beats carry no "
                         f"character at all: {naked}")
    missing: set[str] = set()
    for beat in beats:
        scene = by_number.get(beat.scene_number, {})
        for who in people_in(scene):
            if f"char-{who}" not in refs:
                missing.add(who)
    if missing:
        print(f"  note: {len(missing)} characters appear in chosen scenes with no "
              f"reference sheet: {sorted(missing)[:6]}")


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
    lead, figure = lead_of(scenes), figure_of(scenes, lead_of(scenes))
    turn = turn_of(scenes, lead)
    # One image per cut.  Professional trailers run one distinct setup every
    # 2-3 seconds and never reuse one; the shipped cut asked 9 images to carry
    # 31 shots, which forced 23% of the picture to be frames already seen.
    wanted = len(cut_points(cue["title_stopdown"], cue["grid"])) - 1
    elements = select_setups(scenes, set(refs), wanted, load_iconicity(book))
    if len(elements) < wanted * 0.8:
        raise SystemExit(
            f"REFUSED: {wanted} cuts over {len(elements)} setups is "
            f"{wanted / max(len(elements), 1):.1f} uses per image; render more "
            f"location plates or cut shorter")
    beats = [beat_of(e, i, i / max(len(elements) - 1, 1), refs, lead, figure)
             for i, e in enumerate(elements)]
    refuse_unbindable(beats, scenes, refs)

    restricted = resolution_scenes(scenes, lead, figure)
    candidates = dialogue_candidates(scenes, restricted,
                                     tuple(c for c in (lead, figure) if c))
    # Offer the placer a deep slate: it can only use a line whose
    # speaker is on screen with room to finish, so four candidates
    # yielded one placement.
    lines = pick_lines(candidates, count=16, per_speaker=5)
    points = cut_points(cue["title_stopdown"], cue["grid"])
    shots = shots_for(beats, points, screenplay, refs, lines)

    if {"quiet", "build", "hit"} - {b.arc for b in beats}:
        raise SystemExit("REFUSED: the trailer never reaches a climax")
    appearances = sum(lead in b.cast for b in beats)
    if lead and f"char-{lead}" in refs and appearances < max(3, len(beats) // 4):
        raise SystemExit(f"REFUSED: {lead} leads this story but appears in only "
                         f"{appearances} of {len(beats)} beats")

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

    out = book / "trailer" / trailer_id
    out.mkdir(parents=True, exist_ok=True)
    (out / "plan.json").write_text(plan.model_dump_json(indent=1), encoding="utf-8")
    on_grid = sum(1 for p in points[1:-1] if any(abs(p - g) <= 0.05 for g in cue["grid"]))
    print(f"{len(beats)} setups, {len(shots)} shots, "
          f"{len({b.location_id for b in beats})} locations, "
          f"{len(shots) / len(beats):.2f} shots per setup")
    print(f"  lead {lead} in {appearances} beats; figure {figure}; "
          f"turn sc{turn['number'] if turn else '?'}")
    spoken = [s for s in shots if s.line]
    print(f"  {on_grid}/{len(points) - 2} cuts on a measured onset")
    print(f"  sizes: {', '.join(f'{n}x {s}' for s, n in Counter(s.size for s in shots).most_common())}")
    print(f"  {len(spoken)} spoken lines, {len({s.motion for s in beats})} distinct "
          f"camera moves across {len(beats)} beats -> {out / 'plan.json'}")
    for shot in spoken:
        print(f"    {shot.beat_id} {shot.speaker}: {shot.line[:64]}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "main")
