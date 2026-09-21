"""A panel with no cast must not be framed against a figure.

MEASURED 2026-09-20 on ep06 `beam`, the render immediately after the
example.png dolls were stripped out of the reference slots. The grid's cast
is EMPTY. All four panels are landscape -- a hummock, a line of burning
bushes, three beech crowns, a brick wall. Three of the four came back with a
man standing in them.

The three that did are exactly the three whose framing clause describes a
person: "the panel cuts THE FIGURE at mid-thigh; THE HEAD sits in the upper
third and THE HANDS are visible", and "THE WHOLE FIGURE stands well inside the
panel with open ground below THE FEET and sky above THE HEAD". The fourth,
INSERT, says "the panel comes in close on one subject" and came back clean.

So a size word carries a body with it. Writing "NO NAMED CHARACTER appears in
this panel at all" underneath a figure, a head, feet and hands does not cancel
them -- it is a fence built out of the word being avoided, the same law that
governs MiniMax. When the dolls were still staged the model used a doll to
fill that vacancy; with the dolls gone it draws a man.

A panel's framing must be measured against what the panel actually holds.
"""
from __future__ import annotations

import pytest

from studio.storyboard_grid import BODY_WORDS, cut_clause

SIZES = ("wide", "medium", "medium_close", "close", "insert")


@pytest.mark.parametrize("size", SIZES)
def test_an_empty_panel_is_never_framed_on_a_body_part(size):
    said = cut_clause(size, peopled=False).lower()
    found = [w for w in BODY_WORDS if w in said]
    assert not found, f"{size} frames an empty panel on {found}"


@pytest.mark.parametrize("size", SIZES)
def test_an_empty_panel_never_says_the_word_it_is_avoiding(size):
    said = cut_clause(size, peopled=False).lower()
    assert "no " not in said and "never" not in said, f"{size} builds a fence: {said}"


def test_a_peopled_panel_still_frames_on_the_figure():
    assert "figure" in cut_clause("medium", peopled=True)


@pytest.mark.parametrize("size", SIZES)
def test_every_size_says_something_for_an_empty_panel(size):
    assert len(cut_clause(size, peopled=False).split()) >= 8


def test_an_unknown_size_is_refused():
    with pytest.raises(KeyError):
        cut_clause("extreme_close", peopled=False)
