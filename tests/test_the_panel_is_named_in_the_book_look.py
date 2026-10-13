"""The take is told what its storyboard panel IS in the book's own look.

Jekyll ep01 (2026-10-13, LOOK.md cause 1): every take's subject_definitions said
the photoreal panel was drawn "in the house art style" (studio/take_refs.py) --
H3 was told a film still was a painting.  A book with no declaration keeps the
words byte for byte.
"""
from __future__ import annotations

import json
from pathlib import Path

from studio import book_look, house_style, take_refs

HOUSE = ("<Picture 3> is the storyboard frame drawn for this shot: the place, the people "
         "in it and the clothes they wear, at this hour of the day, in the house art style.")


def declare(book: Path) -> Path:
    (book / "refs").mkdir(parents=True, exist_ok=True)
    (book / "refs" / "look.json").write_text(json.dumps({"look": "photoreal", "lead": "Photo. "}),
                                              encoding="utf-8")
    return book


def test_the_house_definition_is_byte_for_byte():
    assert take_refs.panel_definition(3) == HOUSE


def test_a_photoreal_panel_is_a_photographic_frame_and_never_a_still():
    said = take_refs.panel_definition(3, book_look.panel_look_words(True))
    assert "house art style" not in said and "photographic frame" in said and "still" not in said
    assert said.startswith("<Picture 3> is the storyboard frame drawn for this shot")


def test_the_book_decides_the_words(tmp_path):
    assert book_look.panel_look(tmp_path) == book_look.PANEL_HOUSE
    assert "photographic" in book_look.panel_look(declare(tmp_path))


def test_the_run_adopts_them_and_resets():
    try:
        house_style.adopt_panel_look(book_look.panel_look_words(True))
        assert "photographic" in house_style.panel_look()
    finally:
        house_style.adopt_panel_look("")
    assert house_style.panel_look() == book_look.PANEL_HOUSE


def test_a_drawn_look_names_the_panel_in_its_own_words(tmp_path):
    (tmp_path / "refs").mkdir()
    (tmp_path / "refs" / "look.json").write_text(json.dumps({"look": "anime_gothic", "lead": "Anime. "}),
                                                 encoding="utf-8")
    said = book_look.panel_look(tmp_path)
    assert said == "in the book's own anime gothic look" and "still" not in said
