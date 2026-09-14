"""`picture_path` is the ONE place a bare reference name becomes a file, so every
branch of it has to be walked by a test.

It was not.  `from __future__ import annotations` makes `boards: Path` a string
at import time, so the module needed no `pathlib` import to define the function
-- and the only line that touches `Path` at RUNTIME is the `char-` branch.  The
module imported, the whole suite passed, and the failure waited until a take
asked for a cast card:

    NameError: name 'Path' is not defined   (takes_r2v graph_for, episode 4)

The class is worth naming: under `from __future__ import annotations` a missing
import is invisible until the one statement that uses it executes.  The guard is
not a linter, it is a test that walks every branch.
"""
from pathlib import Path

from studio.episode_seq_board import picture_path

BOARDS = Path("book/episodes/ep04/boards")
BOOK = Path("book")


def test_a_cast_card_goes_to_the_books_characters():
    got = picture_path(BOARDS, BOOK, "char-john_rance_indoor.png")
    assert got == BOOK / "refs" / "characters" / "char-john_rance_indoor.png"


def test_a_plate_goes_to_the_episodes_plates():
    assert picture_path(BOARDS, BOOK, "plate_cab.png") == BOARDS / "plates" / "plate_cab.png"


def test_a_sheet_goes_to_the_episodes_sheets():
    assert picture_path(BOARDS, BOOK, "seq_cab_0.png") == BOARDS / "sheets" / "seq_cab_0.png"


def test_a_panel_goes_to_the_episodes_panels():
    assert picture_path(BOARDS, BOOK, "panel_Q11_0.png") == BOARDS / "panels" / "panel_Q11_0.png"


def test_a_before_picture_is_a_panel_whatever_it_is_called():
    got = picture_path(BOARDS, BOOK, "Q11_0.before.png")
    assert got == BOARDS / "panels" / "Q11_0.before.png"


def test_anything_else_is_a_cell():
    assert picture_path(BOARDS, BOOK, "Q11_0E.png") == BOARDS / "cells" / "Q11_0E.png"


def test_every_branch_returns_a_real_path_object():
    """The NameError shape: a branch that builds no Path at all."""
    names = ["char-x.png", "plate_x.png", "seq_x_0.png", "panel_x.png", "x.before.png", "Q00_0.png"]
    assert all(isinstance(picture_path(BOARDS, BOOK, n), Path) for n in names)
