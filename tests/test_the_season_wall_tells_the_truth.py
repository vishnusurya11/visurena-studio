"""Board review 2026-10-12: the book page's season wall
- 02 #6: drew `⚑26` on 16 published WotW tiles whose flags views.flags_open
  calls closed (the 181e7e1 bug surviving on one template);
- 02 #13 / 01 B12 / 03 A3: put ep14 (sequence NULL) first on the book page
  and last in the department; one key orders both: the unit's number;
- 02 #12 / 03 A4: said "no picture yet" for 18 shipped episodes that have
  board panels, reference takes or contact sheets.  $0."""
from __future__ import annotations

import json

import pytest

from command_center_fixtures import CODEX, make_library, seed
from studio import db
from studio.command_center import views, viz


@pytest.fixture()
def library(tmp_path, monkeypatch):
    return make_library(tmp_path, monkeypatch)


@pytest.fixture()
def conn(tmp_path, library):
    connection = db.get_connection(tmp_path / "t.db")
    db.init_db(connection)
    db.insert_codex(connection, "A Book", codex_id=CODEX)
    seed(connection, library)
    return connection


def _publish_ep03(library):
    with open(library / f"{CODEX}_a-book" / "uploads.jsonl", "a", encoding="utf-8") as fh:
        fh.write(json.dumps({"episode": 3, "video_id": "abc", "sha8": "0badf00d", "privacy": "public"}) + "\n")


def test_a_published_tile_shows_no_open_flags(conn, library):
    row = dict(db.work_order(conn, CODEX, "episode", "ep03"))
    assert row["flags"] > 0 and views.row_view(row, conn)["flags_open"] == row["flags"]
    _publish_ep03(library)
    assert views.row_view(row, conn)["flags_open"] == 0


def test_the_unit_number_orders_a_row_without_a_sequence():
    rows = [{"unit": "ep14", "sequence": None, "number": None}, {"unit": "ep01", "sequence": 1, "number": 1},
            {"unit": "ep02", "sequence": 2, "number": 2}, {"unit": "main", "sequence": None, "number": None}]
    assert [r["unit"] for r in sorted(rows, key=views.unit_order)] == ["ep01", "ep02", "ep14", "main"]


def test_the_season_rows_come_in_episode_order(conn):
    db.upsert_work_order(conn, CODEX, "episode", "ep14", state="done", sequence=None, number=None)
    units = [r["unit"] for r in views.season_rows(conn, CODEX)]
    assert units == sorted(units, key=lambda u: int(u[2:])) and units[-1] == "ep14"


def test_attention_rank_breaks_ties_by_the_unit_number():
    a = {"unit": "ep14", "sequence": None, "number": None, "state": "done", "shown": "done"}
    b = {"unit": "ep15", "sequence": 15, "number": 15, "state": "done", "shown": "done"}
    assert sorted([b, a], key=views.rank)[0]["unit"] == "ep14"


@pytest.mark.parametrize("files,expected", [
    (["boards/panels/p0.png", "boards/panels/p1.png", "boards/panels/p2.png"], "boards/panels/p1.png"),
    (["boards/ref_take_00.png", "boards/ref_take_01.png", "boards/ref_take_02.png", "boards/ref_take_03.png",
      "boards/ref_take_04.png"], "boards/ref_take_02.png"),
    (["review/contact_aaaa.png"], "review/contact_aaaa.png"),
])
def test_a_shipped_episode_without_a_storyboard_still_has_a_poster(tmp_path, files, expected):
    home = tmp_path / "ep01"
    for rel in files:
        (home / rel).parent.mkdir(parents=True, exist_ok=True)
        (home / rel).write_bytes(b"png")
    assert viz.poster_file(home).relative_to(home).as_posix() == expected
