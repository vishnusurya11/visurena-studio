r"""A reference the bible declares must exist, or the draw is unbound and silent.

MEASURED, episode 7. `refs.json` gained a `terrier` prop row, and the note
written with it says exactly why:

    "Chapter VII. It appears alive, drinking and dead across three shots, so its
     identity has to hold like a character's."

`refs/props/prop-terrier.png` was never drawn. And `seq_boards.draw_setup` has

    shown = [r for r in shown if (book / r['rel_path']).exists()]      # line 266

so the one prop in the episode whose identity was explicitly declared to need
binding is the one prop that was silently dropped from the reference list. Three
sheets were drawn at $0.13 each with the dog unbound, and nothing anywhere said
so. The dog happened to come out consistent; that was luck, and luck is not a
gate.

Seventh instance in this session of the same shape: a computation whose empty
result is indistinguishable from a clean one.

The rule is narrow on purpose. It does not ask that every prop have a reference
-- most do not need one. It asks that a row SOMEBODY WROTE INTO THE BIBLE point
at a file that exists. Declaring a reference and not drawing it is never
intentional; if the reference is not wanted, the row should not be there.

It is HARD, and it runs in `seq_boards` before the first paid sheet, because the
cost of being wrong is a $0.13 draw with the wrong references attached plus the
re-draw and the re-render to correct it.
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from studio import prop_refs

BOOK = ROOT / "library/20260822113400_a-study-in-scarlet"


def rows(tmp_path, *specs):
    made = []
    for entity, draw in specs:
        rel = f"refs/props/prop-{entity}.png"
        if draw:
            p = tmp_path / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(b"\x89PNG\r\n\x1a\n")
        made.append({"ref_id": f"prop-{entity}", "kind": "prop", "entity_id": entity,
                     "name": entity, "rel_path": rel})
    return made


def test_a_row_with_no_picture_is_named(tmp_path):
    said = prop_refs.undrawn(rows(tmp_path, ("terrier", False), ("violin", True)), tmp_path)
    assert len(said) == 1
    assert "terrier" in said[0]
    assert "refs/props/prop-terrier.png" in said[0]


def test_a_bible_whose_pictures_all_exist_says_nothing(tmp_path):
    assert prop_refs.undrawn(rows(tmp_path, ("violin", True), ("pencil", True)), tmp_path) == []


def test_characters_and_locations_are_checked_too(tmp_path):
    """The fault is a declared reference with no file, whatever kind it is."""
    p = tmp_path / "refs/characters/char-holmes.png"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b"\x89PNG\r\n\x1a\n")
    refs = [{"kind": "character", "entity_id": "sherlock_holmes",
             "rel_path": "refs/characters/char-holmes.png"},
            {"kind": "character", "entity_id": "brigham_young",
             "rel_path": "refs/characters/char-brigham_young.png"}]
    said = prop_refs.undrawn(refs, tmp_path)
    assert len(said) == 1 and "brigham_young" in said[0]


def test_a_row_with_no_rel_path_at_all_is_named(tmp_path):
    refs = [{"kind": "prop", "entity_id": "ghost"}]
    assert prop_refs.undrawn(refs, tmp_path)


def test_the_delivered_bible_is_measured_here_not_assumed():
    """The live bible. This failed when written -- `terrier` was the one row --
    and it is the check that would have said so before episode 7 was drawn."""
    if not (BOOK / "refs/refs.json").exists():
        pytest.skip("the book is not on this disk")
    refs = json.loads((BOOK / "refs/refs.json").read_text(encoding="utf-8"))["refs"]
    assert prop_refs.undrawn(refs, BOOK) == []
