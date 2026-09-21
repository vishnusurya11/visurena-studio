"""A panel with no cast says what it IS, not who is missing from it.

The companion to test_an_empty_panel_is_not_framed_on_a_person. That one
stopped the framing from describing a body; this one stops the peopling clause
from naming a character.

"NO NAMED CHARACTER appears in this panel at all" puts `character` into the
sentence and takes nothing out of the picture. The same fence the MiniMax
prompts are forbidden to build.
"""
from __future__ import annotations

from studio.storyboard_grid import panel_block, peopling_clause


def test_an_empty_panel_never_names_a_character():
    said = peopling_clause([]).lower()
    for word in ("character", "person", "people", "figure", "nobody", "no one"):
        assert word not in said, f"an empty panel says {word!r}: {said}"


def test_an_empty_panel_still_says_something():
    assert len(peopling_clause([]).split()) >= 5


def test_a_peopled_panel_names_exactly_who_stands_in_it():
    said = peopling_clause(["STENT", "OGILVY"])
    assert "STENT" in said and "OGILVY" in said


def test_the_block_carries_the_clause_through():
    block = panel_block(1, "top-left", "WIDE", "A hummock of sand.",
                        "the camera stands far back", who=[])
    assert "NO NAMED CHARACTER" not in block
    assert peopling_clause([]) in block


def test_a_peopled_block_still_bounds_its_cast():
    block = panel_block(1, "top-left", "WIDE", "Two men.", "cut", who=["STENT"])
    assert "STENT" in block and "no other named person" in block
