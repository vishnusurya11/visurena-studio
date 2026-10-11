"""A look is ONE derivation of the character's base sheet (owner 2026-10-10:
never an edit of an edit, never a composite).  The look table refuses a look
whose parent is anything but the base sheet."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from studio.continuity_spec import CharacterLooks, LookBook


def card(**over) -> dict:
    doc = {"base": "day_suit", "base_sha8": "aaaa1111", "body": "Man of 34, slender, grey eyes.",
           "looks": {"day_suit": {"made_by": "base", "markers": {"hair_colour": "dark"}},
                     "ragged": {"made_by": "edit", "parent_sha8": "aaaa1111",
                                "sheet": "refs/characters/n/looks/ragged.png",
                                "markers": {"hair_colour": "grey", "facial_hair": "beard"}}},
           "timeline": [{"look": "day_suit", "start": {"chapter": 1}},
                        {"look": "ragged", "start": {"chapter": 22}}]}
    doc.update(over)
    return doc


def test_a_look_drawn_from_the_base_is_accepted():
    assert CharacterLooks.model_validate(card()).looks["ragged"].parent_sha8 == "aaaa1111"


def test_a_look_drawn_from_another_look_is_refused():
    bad = card()
    bad["looks"]["ragged"]["parent_sha8"] = "bbbb2222"
    with pytest.raises(ValidationError, match="one hop"):
        CharacterLooks.model_validate(bad)


def test_an_undrawn_look_names_no_parent_yet():
    doc = card()
    doc["looks"]["ragged"].update(sheet="", parent_sha8="")
    assert CharacterLooks.model_validate(doc).looks["ragged"].sheet == ""


def test_only_the_base_look_is_made_by_base():
    bad = card()
    bad["looks"]["ragged"]["made_by"] = "base"
    with pytest.raises(ValidationError, match="base"):
        CharacterLooks.model_validate(bad)


def test_the_base_must_be_a_defined_look():
    with pytest.raises(ValidationError, match="base"):
        CharacterLooks.model_validate(card(base="nowhere"))


def test_a_marker_outside_the_closed_vocabulary_is_refused():
    bad = card()
    bad["looks"]["ragged"]["markers"]["hair_colour"] = "silvery"
    with pytest.raises(ValidationError):
        CharacterLooks.model_validate(bad)


def test_an_absolute_sheet_path_is_refused():
    bad = card()
    bad["looks"]["ragged"]["sheet"] = "D:/library/x/refs/characters/n/looks/ragged.png"
    with pytest.raises(ValidationError, match="relative"):
        CharacterLooks.model_validate(bad)


def test_the_book_resolves_a_look_by_story_time():
    book = LookBook.model_validate({"book": "b", "characters": {"n": card()}})
    assert book.look_id_at("n", 21) == "day_suit"
    assert book.look_id_at("n", 22) == "ragged"
    assert book.look_id_at("nobody", 22) == ""
