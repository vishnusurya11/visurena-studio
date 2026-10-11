"""The CPU replay of G-LOOK / G-PLACE over a finished book judges each plan
against what was drawn BEFORE it (anchors + views earlier plans staged), reads
the look table from the dossiers when the book has none, and counts
G-LOOK-WORDS as an advisory only."""
from __future__ import annotations

import json
from types import SimpleNamespace

from studio.continuity_spec import CharacterLooks, LookBook
from tests import continuity_fixtures as fx
from tests.test_a_place_is_its_master import book

from scripts.refs import continuity_replay as replay


def test_a_view_first_staged_later_was_not_drawn_before(tmp_path):
    b = book(tmp_path)
    drawn = replay.drawn_before(b, 1)
    assert drawn(b, "narrators_home") == ["wide_establishing"]           # dining view not yet staged


def test_the_table_comes_from_the_dossiers_when_the_book_has_none(tmp_path):
    b = book(tmp_path)
    (b / "analysis" / "characters").mkdir()
    (b / "analysis" / "characters" / "n.json").write_text(json.dumps({"profile": {
        "physical": "A man.", "wardrobe": {"suit": "A suit."}, "wardrobe_by_chapter": {"1": "suit"}}}))
    assert replay.table_of(b).look_id_at("n", 3) == "suit"


def test_prose_naming_another_hair_is_an_advisory():
    table = LookBook(characters={"narrator": CharacterLooks.model_validate(fx.CARD)})
    shot = SimpleNamespace(index=4, faces=["narrator"], frame="He pushes back his dark hair.", at_rest="")
    got = replay.word_advisories(table, SimpleNamespace(number=24, shots=[shot]))
    assert got and "G-LOOK-WORDS shot 4" in got[0]
