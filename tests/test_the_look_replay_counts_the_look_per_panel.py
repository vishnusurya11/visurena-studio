"""The acceptance replay's pure parts (the GPU parts run only in an owner-
approved window): cells cut row by row, a panel shows a look when its hair
family AND facial hair match, the pass share is 80 %."""
from __future__ import annotations

from studio.continuity_spec import CharacterLooks, LookBook, Markers
from tests import continuity_fixtures as fx

from scripts.refs import look_replay as replay

RAGGED = Markers(hair_colour="grey", facial_hair="beard")


def test_cells_are_cut_row_by_row():
    assert replay.panel_boxes(2048, 1024, 2, 1) == [(0, 0, 1024, 1024), (1024, 0, 2048, 1024)]


def test_a_panel_shows_the_look_only_with_its_hair_and_its_beard():
    assert replay.shows_look({"hair_colour": "white", "facial_hair": "beard"}, RAGGED)
    assert not replay.shows_look({"hair_colour": "dark", "facial_hair": "beard"}, RAGGED)
    assert not replay.shows_look({"hair_colour": "grey", "facial_hair": "moustache"}, RAGGED)


def test_the_pass_share_is_eighty_percent():
    good, bad = {"hair_colour": "grey", "facial_hair": "beard"}, {"unread": "x"}
    assert replay.tally([good] * 4 + [bad], RAGGED)["passed"]
    assert not replay.tally([good] * 3 + [bad] * 2, RAGGED)["passed"]


def test_the_staged_looks_are_the_chapters():
    from types import SimpleNamespace
    table = LookBook(characters={"narrator": CharacterLooks.model_validate(fx.CARD)})
    shots = [SimpleNamespace(faces=["narrator", "curate"])]
    assert replay.staged_looks(None, table, SimpleNamespace(number=24), shots) == {"narrator": "ragged"}
