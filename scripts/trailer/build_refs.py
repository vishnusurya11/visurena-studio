#!/usr/bin/env python
"""Generate the reference sheets a book's trailer, song and episode all share.

Writes library/<book>/refs/{characters,locations}/*.png plus refs.json, which
records the prompt each sheet was made from.  The prompt is kept because the
character's physical description has to be repeated VERBATIM in every shot
prompt later: the reference pins the instance, the words pin the category, and
dropping either one lets the face drift.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio.comfy import run
from studio.trailer_plan import pick_scenes, speaking_characters, unique_locations
from studio.trailer_refs import (character_prompt, load_json, location_prompt,
                                 physical_of, ref_id_for)

LIBRARY = Path(__file__).resolve().parents[2] / "library"
SEED_BASE = 40000


def book_dir(book_id: str) -> Path:
    hits = [p for p in LIBRARY.iterdir() if p.name.startswith(book_id) or p.name == book_id]
    if not hits:
        raise SystemExit(f"no book matching {book_id!r}")
    return hits[0]


def refs_needed(book: Path, count: int) -> tuple[list[str], list[str]]:
    """Which characters and locations this book's trailer will have to show."""
    screenplay = load_json(book / "screenplay/feature/screenplay.json")
    scenes = screenplay["scenes"]
    picked = pick_scenes(scenes, count, None)
    speakers = [c for c in speaking_characters(picked)][:6]
    return speakers, unique_locations(picked)[:7]


def describe_location(book: Path, loc_id: str, scenes: list[dict]) -> str:
    """A plate description, preferring analysis, falling back to the slug."""
    path = book / "analysis/locations" / f"{loc_id}.json"
    if path.exists():
        described = (load_json(path).get("profile") or {}).get("physical", "")
        if described.strip():
            return described.strip()
    for scene in scenes:
        if scene.get("slug", {}).get("location_id") == loc_id:
            return scene["slug"]["location_name"]
    return loc_id.replace("_", " ")


def generate(prompt: str, prefix: str, seed: int, dest: Path) -> Path:
    """Render one sheet and move it into the book's refs folder."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        return dest
    written = run("image_krea2_turbo_t2i", {
        "prompt": prompt, "aspect_ratio": "16:9 (Widescreen)", "megapixels": 1.0,
        "seed": seed, "steps": 8, "filename_prefix": prefix})
    if not written:
        raise RuntimeError(f"{prefix} produced no image")
    dest.write_bytes(written[0].read_bytes())
    return dest


def main(book_id: str, palette: str, scene_count: int = 12) -> None:
    book = book_dir(book_id)
    screenplay = load_json(book / "screenplay/feature/screenplay.json")
    characters, locations = refs_needed(book, scene_count)
    refs_root = book / "refs"
    record: list[dict] = []

    for index, char_id in enumerate(characters):
        path = book / "analysis/characters" / f"{char_id}.json"
        if not path.exists():
            print(f"  SKIP character {char_id}: no analysis")
            continue
        character = load_json(path)
        physical = physical_of(character)
        prompt = character_prompt(physical, palette)
        ref_id = ref_id_for("character", char_id)
        dest = refs_root / "characters" / f"{ref_id}.png"
        print(f"  [{index + 1}/{len(characters)}] {ref_id}")
        generate(prompt, f"REF-{ref_id}", SEED_BASE + index, dest)
        record.append({"ref_id": ref_id, "kind": "character", "entity_id": char_id,
                       "name": character.get("name", char_id), "physical": physical,
                       "prompt": prompt, "rel_path": f"refs/characters/{ref_id}.png"})

    for index, loc_id in enumerate(locations):
        described = describe_location(book, loc_id, screenplay["scenes"])
        prompt = location_prompt(described, palette)
        ref_id = ref_id_for("location", loc_id)
        dest = refs_root / "locations" / f"{ref_id}.png"
        print(f"  [{index + 1}/{len(locations)}] {ref_id}")
        generate(prompt, f"REF-{ref_id}", SEED_BASE + 500 + index, dest)
        record.append({"ref_id": ref_id, "kind": "location", "entity_id": loc_id,
                       "name": described[:90], "physical": described,
                       "prompt": prompt, "rel_path": f"refs/locations/{ref_id}.png"})

    (refs_root / "refs.json").write_text(
        json.dumps({"book_id": book.name, "palette": palette, "refs": record},
                   indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"{len(record)} refs -> {refs_root}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "")
