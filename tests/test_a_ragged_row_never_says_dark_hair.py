"""The bound row of a character in a face-changing look carries ONE head, and
the markers the content gates compare (retro 2026-10-10: ep25 T05's subject
line said "Dark brown hair ... shaven" and "ash-grey ... beard" at once)."""
from __future__ import annotations

import json

from studio import pack_refs

BODY = ("Man of 34, slender, grey eyes. Dark brown hair cut short, parted on the left. "
        "Neat close-trimmed dark brown moustache; shaven cheeks and chin.")
WARDROBE = {"day_suit": "Mid-grey tweed lounge suit. Straw boater with a black band.",
            "ragged_greyed": "Torn flannel shirt, battered brown felt hat. Hair turned ash-grey throughout; "
                             "sixteen days of grey-brown beard; face gaunt."}


def book(tmp_path):
    folder = tmp_path / "analysis" / "characters"
    folder.mkdir(parents=True)
    (folder / "narrator.json").write_text(json.dumps({"name": "The Narrator", "profile": {
        "physical": BODY, "wardrobe": WARDROBE,
        "wardrobe_by_chapter": {"1": "day_suit", "22": "ragged_greyed"}}}), encoding="utf-8")
    return tmp_path


def test_the_ragged_row_has_one_head(tmp_path):
    row = pack_refs.character_row(book(tmp_path), "narrator", 24)
    assert "Dark brown hair" not in row["physical"] and "shaven" not in row["physical"]
    assert row["physical"].startswith("Hair turned ash-grey")
    assert row["markers"]["hair_colour"] == "grey" and row["markers"]["facial_hair"] == "beard"
    assert row["look"] == "ragged_greyed"


def test_the_first_look_keeps_its_old_bytes(tmp_path):
    row = pack_refs.character_row(book(tmp_path), "narrator", 3)
    assert row["physical"] == f"{BODY} Wearing: {WARDROBE['day_suit']}"
    assert row["markers"]["hair_colour"] == "dark" and row["markers"]["headwear"] == "boater"
