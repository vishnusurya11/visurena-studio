"""Board review 2026-10-12:
- 02 #15: published units read "11 qc · 4/12", "step 11 of 13" -- the cursor the
  09-26 backfill froze; a done row is at its last step with no progress;
- 02 #11: "Moved 20 h" on episodes published weeks ago -- every tick upsert bumps
  updated_at; Moved is the unit's newest event, else when it finished;
- 02 #12 / 03 A19: /books said "1 making episodes" (WotW, complete) and left
  Scarlet (14 episodes) on the shelf; the book page counted 29 units where /books
  counted 31; the shelf printed raw codex ids.  $0."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from command_center_fixtures import CODEX, make_app, make_library, seed
from studio import db, registry
from studio.command_center import views

LAST = registry.steps("episode")[-1]


@pytest.fixture()
def conn(tmp_path, monkeypatch):
    library = make_library(tmp_path, monkeypatch)
    connection = db.get_connection(tmp_path / "t.db")
    db.init_db(connection)
    db.insert_codex(connection, "A Book", codex_id=CODEX)
    seed(connection, library)
    return connection


def test_a_done_row_stands_at_its_last_step_without_progress(conn):
    db.upsert_work_order(conn, CODEX, "episode", "ep03", step_id="11", progress="4/12")
    v = views.row_view(db.work_order(conn, CODEX, "episode", "ep03"), conn)
    assert (v["step_id"], v["step_name"], v["progress"]) == (LAST["id"], LAST["name"], None)


def test_a_running_row_keeps_its_cursor(conn):
    v = views.row_view(db.work_order(conn, CODEX, "episode", "ep04"), conn)
    assert v["step_id"] == "09" and v["progress"] == "18/25"


def test_moved_is_the_newest_event_not_the_last_upsert():
    row = {"updated_at": "2026-10-11T17:38:00Z", "finished_at": "2026-09-12T20:00:00Z"}
    assert views.moved_at(row, "2026-09-12T21:00:00Z") == "2026-09-12T21:00:00Z"
    assert views.moved_at(row, None) == "2026-09-12T20:00:00Z"
    assert views.moved_at({"updated_at": "2026-10-11T17:38:00Z"}, None) == "2026-10-11T17:38:00Z"


def test_the_department_reads_each_units_newest_event(conn):
    moves = views.last_moves(conn, "episode")
    newest = conn.execute("SELECT MAX(event_ts) FROM events WHERE unit = 'ep05'").fetchone()[0]
    assert moves[(CODEX, "ep05")] == newest and (CODEX, "ep06") not in moves


def test_making_episodes_means_an_episode_not_yet_done(conn):
    shelf = {b["codex_id"]: b for b in views.shelf(conn)}
    assert shelf[CODEX]["episodes"] >= 4 and shelf[CODEX]["open_episodes"] >= 1
    for unit in ("ep04", "ep05", "ep06", "ep07"):
        db.upsert_work_order(conn, CODEX, "episode", unit, state="done", lease_until=None)
    shelf = {b["codex_id"]: b for b in views.shelf(conn)}
    assert shelf[CODEX]["open_episodes"] == 0


def test_the_book_page_counts_units_as_the_shelf_does(tmp_path, monkeypatch):
    c = TestClient(make_app(tmp_path, monkeypatch))
    conn = db.get_connection(tmp_path / "t.db")
    for stage in ("analysis", "screenplay"):          # two rows, one unit name (`book`)
        db.upsert_work_order(conn, CODEX, stage, "book", state="done")
    n = conn.execute("SELECT COUNT(*) FROM work_orders WHERE codex_id = ?", (CODEX,)).fetchone()[0]
    assert f"<b>{n}</b><span>units</span>" in c.get(f"/b/{CODEX}").text


def test_the_shelf_prints_no_raw_codex_id(tmp_path, monkeypatch):
    from command_center_fixtures import OTHER
    html = TestClient(make_app(tmp_path, monkeypatch)).get("/books").text
    assert f">{OTHER}<" not in html and f">{CODEX}<" not in html
