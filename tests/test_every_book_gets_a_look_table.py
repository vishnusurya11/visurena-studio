"""refs 01_03: every bound character gets its looks in refs/looks.json -- from
the dossier's own costume plot when it has one, else from the look-timeline
writer (a FakeModel here; no test spends).  A character already in the table
is never rewritten, so a drawn look keeps its picture."""
from __future__ import annotations

import json

from scripts.refs import looks_table
from tests.test_episode_writer import FakeModel

DRAFT = {"looks": [{"look_id": "travel_coat", "start_chapter": 1, "top": "dark overcoat"}]}


def book(tmp_path):
    folder = tmp_path / "analysis" / "characters"
    folder.mkdir(parents=True)
    (folder / "griffin.json").write_text(json.dumps({"id": "griffin", "profile": {"physical": "Tall man. Dark hair cut short."}}),
                                         encoding="utf-8")
    (folder / "narrator.json").write_text(json.dumps({"id": "narrator", "profile": {
        "physical": "A man. Fair hair parted on the left.", "wardrobe": {"suit": "A grey suit."}, "wardrobe_by_chapter": {"1": "suit"}}}),
        encoding="utf-8")
    return tmp_path


def test_a_costume_plot_is_read_and_a_ledger_is_written_by_the_agent(tmp_path):
    fake = FakeModel(DRAFT)
    written = looks_table.build(book(tmp_path), ["griffin", "narrator"], _agent=fake)
    assert written == ["griffin", "narrator"] and len(fake.prompts) == 1
    doc = json.loads((tmp_path / "refs" / "looks.json").read_text(encoding="utf-8"))
    assert doc["characters"]["narrator"]["base"] == "suit"
    assert doc["characters"]["griffin"]["base"] == "travel_coat"


def test_a_character_already_in_the_table_is_left_alone(tmp_path):
    looks_table.build(book(tmp_path), ["griffin"], _agent=FakeModel(DRAFT))
    fake = FakeModel(DRAFT)
    assert looks_table.build(tmp_path, ["griffin"], _agent=fake) == []
    assert fake.prompts == []
