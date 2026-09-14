"""The book is FOUND, never counted to.

`book_of` was `Path(out).resolve().parents[3]`, with the docstring "the book
folder above `episodes/epNN/frames/<file>`" -- a hard-coded DEPTH, correct for
exactly one layout.

MEASURED 2026-09-13, the hour the sheets moved into `boards/sheets/`: seven
paid gpt-image calls, $0.91 of real money, were recorded into
`library/<book>/episodes/spend.jsonl` instead of `library/<book>/spend.jsonl`.
Nothing failed and nothing was logged as wrong; the book's ledger simply
under-reported by $0.91 and the episode looked like it had cost $0.08.

A ledger that can be silently written to the wrong file is worse than no ledger,
because it is read as complete.  So the book is now identified by what a book
HAS -- a `refs/` folder and an `episodes/` folder -- and the walk stops when it
finds one, at any depth.
"""
from pathlib import Path

import pytest

from studio import book_root


def a_book(tmp_path: Path) -> Path:
    book = tmp_path / "library" / "20260822113400_a-study-in-scarlet"
    (book / "refs").mkdir(parents=True)
    (book / "episodes").mkdir(parents=True)
    return book


def test_the_old_depth_the_sheets_used_to_live_at(tmp_path):
    """`episodes/ep04/frames/seq_cab_0.png` -- three levels up."""
    book = a_book(tmp_path)
    out = book / "episodes" / "ep04" / "frames" / "seq_cab_0.png"
    out.parent.mkdir(parents=True)
    assert book_root.of(out) == book


def test_the_new_depth_the_sheets_live_at_now(tmp_path):
    """`episodes/ep04/boards/sheets/seq_cab_0.png` -- FOUR levels up, and the
    $0.91 that went to the wrong ledger."""
    book = a_book(tmp_path)
    out = book / "episodes" / "ep04" / "boards" / "sheets" / "seq_cab_0.png"
    out.parent.mkdir(parents=True)
    assert book_root.of(out) == book


def test_a_panel_redraw_two_rooms_deep(tmp_path):
    book = a_book(tmp_path)
    out = book / "episodes" / "ep04" / "boards" / "panels" / "panel_Q10_0.png"
    out.parent.mkdir(parents=True)
    assert book_root.of(out) == book


def test_a_take_under_its_engine_and_its_attempts(tmp_path):
    book = a_book(tmp_path)
    out = book / "episodes" / "ep04" / "takes" / "r2v" / "attempts" / "T14_fail2.mp4"
    out.parent.mkdir(parents=True)
    assert book_root.of(out) == book


def test_a_character_card_beside_the_book(tmp_path):
    book = a_book(tmp_path)
    out = book / "refs" / "characters" / "char-john_rance_indoor.png"
    out.parent.mkdir(parents=True)
    assert book_root.of(out) == book


def test_a_path_outside_any_book_raises_rather_than_guessing(tmp_path):
    """Silently choosing a folder is how the money went to the wrong file."""
    stray = tmp_path / "somewhere" / "else.png"
    stray.parent.mkdir(parents=True)
    with pytest.raises(FileNotFoundError, match="no book"):
        book_root.of(stray)


def test_the_nearest_book_wins_when_one_nests(tmp_path):
    book = a_book(tmp_path)
    inner = book / "episodes" / "ep04" / "refs"
    inner.mkdir(parents=True)
    out = book / "episodes" / "ep04" / "boards" / "cells" / "Q00_0.png"
    out.parent.mkdir(parents=True)
    assert book_root.of(out) == book
