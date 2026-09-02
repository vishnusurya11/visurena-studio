#!/usr/bin/env python
"""Bring the 2026-08-25 Sherlock reference sheets into the book's library.

They were good images that nothing downstream ever used.  Moving them under
library/<book>/refs/ with the same ids the rest of the pipeline speaks is what
makes them usable -- and records the physical description beside each one, so
the shot prompts can repeat it verbatim.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio.trailer_refs import character_prompt, load_json, location_prompt, physical_of

ROOT = Path(__file__).resolve().parents[2]
OLD = Path("D:/Projects/KingdomOfViSuReNa/alpha/comfy_studio/poc/"
           "2026-08-25_2k-video-pipeline/outputs/20_sherlock/refs")
BOOK = ROOT / "library/20260822113400_a-study-in-scarlet"
PALETTE = ("Muted desaturated palette of soot-black, gaslight amber and cold London grey; "
           "1881 London; practical Victorian light sources, fog, deep shadow.")

CHARACTERS = {"holmes": "sherlock_holmes", "watson": "john_watson",
              "lestrade": "g_lestrade", "gregson": "tobias_gregson",
              "stamford": "stamford", "hope": "jefferson_hope"}
LOCATIONS = {"221b": "221b_baker_street", "criterion": "criterion_bar",
             "lauriston": "number_3_lauriston_gardens",
             "halliday": "hallidays_private_hotel",
             "alkali_plain": "great_alkali_plain",
             "scotland_yard": "police_station_chamber"}


def main() -> None:
    record: list[dict] = []
    scenes = load_json(BOOK / "screenplay/feature/screenplay.json")["scenes"]

    for old_name, entity_id in CHARACTERS.items():
        source = OLD / f"SH-char-{old_name}.png"
        if not source.exists():
            print(f"  MISSING {source.name}")
            continue
        path = BOOK / "analysis/characters" / f"{entity_id}.json"
        character = load_json(path) if path.exists() else {"name": entity_id}
        physical = physical_of(character)
        ref_id = f"char-{entity_id}"
        dest = BOOK / "refs/characters" / f"{ref_id}.png"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(source.read_bytes())
        record.append({"ref_id": ref_id, "kind": "character", "entity_id": entity_id,
                       "name": character.get("name", entity_id), "physical": physical,
                       "prompt": character_prompt(physical, PALETTE),
                       "rel_path": f"refs/characters/{ref_id}.png"})

    for old_name, entity_id in LOCATIONS.items():
        source = OLD / f"SH-loc-{old_name}.png"
        if not source.exists():
            print(f"  MISSING {source.name}")
            continue
        described = next((s["slug"]["location_name"] for s in scenes
                          if s.get("slug", {}).get("location_id") == entity_id), entity_id)
        ref_id = f"loc-{entity_id}"
        dest = BOOK / "refs/locations" / f"{ref_id}.png"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(source.read_bytes())
        record.append({"ref_id": ref_id, "kind": "location", "entity_id": entity_id,
                       "name": described, "physical": described,
                       "prompt": location_prompt(described, PALETTE),
                       "rel_path": f"refs/locations/{ref_id}.png"})

    (BOOK / "refs/refs.json").write_text(
        json.dumps({"book_id": BOOK.name, "palette": PALETTE, "refs": record},
                   indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"{len(record)} refs -> {BOOK / 'refs'}")


if __name__ == "__main__":
    main()
