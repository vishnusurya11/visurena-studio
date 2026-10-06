"""G-META check 1: the title is COMPOSED from source/book.json and the plan's
own chapter name -- `series_of` + `yp.series_title`, no default, no guess.
The retitle lesson stands behind it: a hardcoded series name ("Sherlock
Holmes") would have renamed another book's published videos, so no book name
may appear in the code under test."""
from __future__ import annotations

from pathlib import Path

import pytest

from scripts.publish import metadata
from tests.publish_fixtures import book_with


def test_the_title_is_the_series_format(tmp_path):
    book = book_with(tmp_path, display_title="The War of the Worlds",
                     series="H. G. Wells", episodes=27, author="H. G. Wells")
    got = metadata.title_for(book, 18, {"title": "The Fifth Cylinder"})
    assert got == 'H. G. Wells: The War of the Worlds — Ep 18/27 — "The Fifth Cylinder"'


def test_a_book_json_without_its_series_fields_is_refused(tmp_path):
    book = book_with(tmp_path, series=None)
    with pytest.raises(SystemExit, match="series"):
        metadata.title_for(book, 1, {"title": "A Chapter"})


def test_no_book_name_is_hardcoded_in_the_module():
    source = Path(metadata.__file__).read_text(encoding="utf-8")
    for name in ("Sherlock", "Scarlet", "Wells", "Worlds", "Keeper", "Lantern"):
        assert name not in source, f"{name!r} is typed into metadata.py; it must come from the book"
