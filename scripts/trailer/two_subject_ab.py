"""Does H3 keep two faces apart?  One beat, the same seeds, rendered bound to
(principal, place) and to (principal, second person); BOTH faces read back.

Every beat binds one sheet by design -- `build_plan.beat_of` casts one
principal and the second slot carries the place -- so in the run-6b trailer
all fourteen takes referenced Holmes and the Watson beside him was a
different clean-shaven man each time.  H3 takes two references.  Whether a
second face in the second slot binds, and whether it costs the first face
anything, is a measurement, not a guess.  Local GPU only; spends nothing.

    uv run python -m scripts.trailer.two_subject_ab 20260822113400 --beat B05 \\
        --second john_watson --seeds 3
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.trailer.build_clips import ROOT, bound_slots, render_take, take_values
from scripts.trailer.step_07_clips import SEED_BASE, clip_seconds, frames_of, reference_of
from studio.describe import DISTINCT_AT, TraitCard, describe_frames, distance
from studio.trailer_refs import visual_description


def pair_beat(beat: dict, second: str) -> dict:
    """The same beat with the second person in its cast."""
    return {**beat, "cast": [*beat["cast"], second]}


def variants(beat: dict, refs: dict, second: str) -> dict[str, tuple[dict, list[str]]]:
    """The control binds the principal and the place; the treatment binds two people."""
    pair = pair_beat(beat, second)
    return {"one": (beat, bound_slots(beat, refs)), "two": (pair, bound_slots(pair, refs))}


def cue_for(ref: dict) -> str:
    """How the reader singles one person out of a two-shot: their own sheet's look."""
    return visual_description(ref["physical"])


def read_faces(take: Path, work: Path, seed: int, people: dict[str, tuple[TraitCard, str]]) -> dict:
    """Each expected person read out of the take by their cue, against their sheet."""
    frames = frames_of(take, clip_seconds(take), work)
    faces = {}
    for ref_id, (reference, cue) in people.items():
        card = describe_frames(frames, seed=seed, whom=cue)
        apart = distance(card, reference)
        faces[ref_id] = {"distance": apart, "bound": apart < DISTINCT_AT}
    return faces


def run_ab(book: Path, out_dir: Path, variants: dict, plan: dict, refs: dict, style: str,
           people: dict[str, tuple[TraitCard, str]], seeds: list[int]) -> list[dict]:
    """Every seed through both bindings; one JSON line per take as it lands."""
    out_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    with (out_dir / "two_subject.jsonl").open("a", encoding="utf-8") as log:
        for name, (beat, bound) in variants.items():
            for seed in seeds:
                values = take_values(beat, plan, refs, style, seed)
                take = render_take(values, bound, refs, book, out_dir / f"{name}-{seed}.mp4")
                expected = {r: people[r] for r in bound if r in people}
                faces = read_faces(take, out_dir / "work" / take.stem, seed, expected)
                rows.append({"variant": name, "seed": seed, "bound_to": bound, "faces": faces,
                             "take": str(take.relative_to(book))})
                log.write(json.dumps(rows[-1]) + "\n")
                log.flush()
    return rows


def summarise(rows: list[dict]) -> dict[str, dict]:
    """Per variant, per face: how many reads, how far from the sheet, how many bound."""
    out: dict[str, dict] = {}
    for row in rows:
        for ref_id, face in row["faces"].items():
            slot = out.setdefault(row["variant"], {}).setdefault(
                ref_id, {"n": 0, "mean_distance": 0.0, "bound": 0})
            slot["n"] += 1
            slot["mean_distance"] += face["distance"]
            slot["bound"] += int(face["bound"])
    for faces in out.values():
        for slot in faces.values():
            slot["mean_distance"] = round(slot["mean_distance"] / slot["n"], 3)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("book_glob")
    parser.add_argument("--beat", default="B05")
    parser.add_argument("--second", default="john_watson")
    parser.add_argument("--seeds", type=int, default=3)
    args = parser.parse_args()
    book = next(p for p in (ROOT / "library").iterdir() if p.name.startswith(args.book_glob))
    out = book / "trailer/main"
    plan = json.loads((out / "plan.json").read_text(encoding="utf-8"))
    refs_doc = json.loads((book / "refs/refs.json").read_text(encoding="utf-8"))
    refs = {r["ref_id"]: r for r in refs_doc["refs"]}
    index, beat = next((i, b) for i, b in enumerate(plan["beats"]) if b["beat_id"] == args.beat)
    both = variants(beat, refs, args.second)
    if len(both["two"][1]) < 2 or not both["two"][1][1].startswith("char-"):
        raise SystemExit(f"{args.beat} + {args.second} does not bind two people: {both['two'][1]}")
    people = {r: (reference_of(book, refs, [r])[1], cue_for(refs[r])) for r in both["two"][1]}
    seeds = [SEED_BASE + index * 7 + 1000 * i for i in range(args.seeds)]
    rows = run_ab(book, out / "ab-two", both, plan, refs, refs_doc["palette"], people, seeds)
    print(json.dumps(summarise(rows), indent=2))


if __name__ == "__main__":
    main()
