"""The look judge names its picture relative to the book; a replay draws outside
the book (docs/audit/.../replay) and must be named, not crash (2026-10-10)."""
from __future__ import annotations

from pathlib import Path

from scripts.refs import looks


def test_a_picture_in_the_book_is_named_relative_to_it(tmp_path):
    book = tmp_path / "book"
    pic = book / "refs" / "looks" / "a.png"
    pic.parent.mkdir(parents=True)
    assert looks.where_of(book, pic) == "refs/looks/a.png"


def test_a_picture_outside_the_book_keeps_its_own_path(tmp_path):
    pic = tmp_path / "replay" / "a.png"
    assert looks.where_of(tmp_path / "book", pic) == Path(pic).resolve().as_posix()
