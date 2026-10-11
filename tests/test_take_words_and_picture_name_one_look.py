"""The step-06 lint: every staged person's picture and words name ONE look on
the book's table, before any grid.  ep18/24/25 T0 changed costume mid-take
because the picture showed one look and the words another."""
from __future__ import annotations

from studio import continuity
from tests import continuity_fixtures as fx


def test_a_bound_drawn_look_is_clean(tmp_path):
    assert continuity.look_faults(fx.book(tmp_path), fx.episode()) == []


def test_a_pick_off_the_table_is_refused(tmp_path):
    got = continuity.look_faults(fx.book(tmp_path), fx.episode({"narrator": "toga"}))
    assert got and "not on the book's look table" in got[0]


def test_an_undrawn_pick_is_refused(tmp_path):
    got = continuity.look_faults(fx.book(tmp_path), fx.episode({"narrator": "borrowed"}))
    assert got and "not drawn" in got[0]


def test_a_row_bound_for_another_look_is_refused(tmp_path):
    got = continuity.look_faults(fx.book(tmp_path, row_look="day_suit"), fx.episode())
    assert got and "rebind" in got[0]


def test_a_book_without_a_table_has_nothing_to_lint(tmp_path):
    assert continuity.look_faults(fx.book(tmp_path, table=False), fx.episode({"narrator": "toga"})) == []
