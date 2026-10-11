"""A non-base look with no picture REFUSES: falling back to the base sheet is
exactly how WotW ep22-27 staged the clean ep01 suit on a grey, bearded man."""
from __future__ import annotations

import pytest

from studio import pack_refs
from tests import continuity_fixtures as fx


def test_the_base_look_is_the_one_sheet(tmp_path):
    book = fx.book(tmp_path)
    assert pack_refs.look_sheet(book, "narrator", "day_suit").name == "sheet.png"
    assert pack_refs.look_sheet(book, "narrator", "").name == "sheet.png"


def test_a_drawn_look_is_its_own_picture(tmp_path):
    book = fx.book(tmp_path)
    assert pack_refs.look_sheet(book, "narrator", "ragged") == \
        book / "refs" / "characters" / "narrator" / "looks" / "ragged.png"


def test_an_undrawn_look_refuses(tmp_path):
    with pytest.raises(SystemExit, match="not drawn"):
        pack_refs.look_sheet(fx.book(tmp_path), "narrator", "borrowed")


def test_a_book_without_a_table_keeps_its_one_sheet(tmp_path):
    book = fx.book(tmp_path, table=False)
    assert pack_refs.look_sheet(book, "narrator", "ragged").name == "sheet.png"
