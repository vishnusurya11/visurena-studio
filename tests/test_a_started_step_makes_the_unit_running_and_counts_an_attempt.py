"""Every event lands on its unit's work-order row from inside add_event (decision
2026-09-25, "events vs rows": one writer, zero runner edits).  The state map:

    started   -> running   (+1 attempt when the started opens a new pass)
    completed -> done on the stage's last step, else running, step_id advanced
    skipped   -> the state stays (a new row stays blocked); step_id moves
    failed / escalated / deferred -> the word

The attempts rule: `attempts` counts PASSES over the unit, not steps started --
a `started` opens a pass unless the row is already running under this very
run_id.  Twelve steps of one run are one attempt; a deferral and the next run's
started are two.  A book-level stage (unit NULL) lands on the unit 'book'.
events.order_id points every event at its row."""
from __future__ import annotations

import pytest

from studio import db

BOOK = "20260901000001"


@pytest.fixture()
def conn(tmp_path):
    connection = db.get_connection(tmp_path / "t.db")
    db.init_db(connection)
    db.insert_codex(connection, "Book", codex_id=BOOK)
    return connection


def _ep(conn, step_id, event, run_id="r1", detail=None):
    db.add_event(conn, BOOK, "episode", step_id, event, run_id=run_id, unit="ep04", detail=detail)


def _row(conn):
    return db.work_order(conn, BOOK, "episode", "ep04")


def test_started_makes_the_unit_running_and_counts_one_attempt(conn):
    _ep(conn, "01", "started")
    row = _row(conn)
    assert (row["state"], row["step_id"], row["run_id"], row["attempts"]) == ("running", "01", "r1", 1)
    assert row["started_at"] and row["updated_at"] and row["finished_at"] is None
    assert (row["home"], row["kind"]) == ("episodes/ep04", "chapter")


def test_the_steps_of_one_run_are_one_attempt(conn):
    for step_id in ("01", "02", "03"):
        _ep(conn, step_id, "started")
        _ep(conn, step_id, "completed")
    assert (_row(conn)["attempts"], _row(conn)["step_id"]) == (1, "03")


def test_a_second_pass_over_the_unit_is_a_second_attempt(conn):
    _ep(conn, "01", "started", run_id="r1")
    _ep(conn, "01", "failed", run_id="r1", detail="REFUSED: no plan")
    assert _row(conn)["state"] == "failed"
    _ep(conn, "01", "started", run_id="r2")
    row = _row(conn)
    assert (row["state"], row["attempts"], row["run_id"]) == ("running", 2, "r2")
    assert row["started_at"] == conn.execute(
        "SELECT event_ts FROM events ORDER BY id LIMIT 1").fetchone()["event_ts"]


def test_the_pass_rule_is_one_function():
    assert db._opens_a_pass(None, "r1") is True
    running = {"state": "running", "run_id": "r1"}
    assert db._opens_a_pass(running, "r1") is False
    assert db._opens_a_pass(running, "r2") is True
    assert db._opens_a_pass({"state": "deferred", "run_id": "r1"}, "r1") is True
    assert db._opens_a_pass({"state": "done", "run_id": "r1"}, "r2") is True


def test_the_state_map_is_a_table():
    assert db.ORDER_STATE_OF_EVENT == {"started": "running", "failed": "failed",
                                       "escalated": "escalated", "deferred": "deferred"}
    assert db.STEP_STATE_OF_EVENT == {"started": "running", "completed": "done"}
    assert db._order_state("episode", "05", "skipped") is None
    assert db._order_state("episode", "05", "escalated") == "escalated"


def test_a_book_level_event_lands_on_the_unit_book(conn):
    db.add_event(conn, BOOK, "analysis", "01", "started", run_id="a1")
    row = db.work_order(conn, BOOK, "analysis", "book")
    assert (row["state"], row["home"], row["kind"]) == ("running", "analysis", "book")
    assert conn.execute("SELECT unit FROM events").fetchone()["unit"] is None


def test_failed_escalated_and_skipped_map_as_specified(conn):
    _ep(conn, "02", "started")
    _ep(conn, "02", "escalated", detail="OWNER PLAN")
    assert _row(conn)["state"] == "escalated"
    _ep(conn, "02", "skipped", run_id="r2", detail="output exists")
    assert (_row(conn)["state"], _row(conn)["step_id"]) == ("escalated", "02")
    _ep(conn, "03", "started", run_id="r2")
    _ep(conn, "03", "failed", run_id="r2", detail="TypeError: x")
    assert (_row(conn)["state"], _row(conn)["step_id"], _row(conn)["attempts"]) == ("failed", "03", 2)


def test_a_skipped_step_on_a_new_row_leaves_it_blocked(conn):
    _ep(conn, "01", "skipped", detail="output exists")
    row = _row(conn)
    assert (row["state"], row["step_id"], row["attempts"]) == ("blocked", "01", 0)
    chip = conn.execute("SELECT * FROM work_steps").fetchone()
    assert (chip["state"], chip["attempt"], chip["detail"]) == ("skipped", 0, "output exists")


def test_every_event_points_at_its_row(conn):
    _ep(conn, "01", "started")
    _ep(conn, "01", "completed")
    db.add_event(conn, BOOK, "refs", "01", "started", run_id="x", unit="main")
    order_ids = [r["order_id"] for r in conn.execute("SELECT order_id FROM events ORDER BY id")]
    assert order_ids[0] == order_ids[1] == _row(conn)["id"]
    assert order_ids[2] == db.work_order(conn, BOOK, "refs", "main")["id"]


def test_the_chip_counts_its_own_starts_and_clips_the_detail(conn):
    _ep(conn, "07", "started")
    _ep(conn, "07", "failed", detail="x" * 500)
    _ep(conn, "07", "started", run_id="r2")
    chip = conn.execute("SELECT * FROM work_steps").fetchone()
    assert (chip["state"], chip["attempt"], chip["run_id"]) == ("running", 2, "r2")
    assert chip["ended_at"] is None and chip["detail"] is None
    _ep(conn, "07", "failed", run_id="r2", detail="y" * 500)
    chip = conn.execute("SELECT * FROM work_steps").fetchone()
    assert len(chip["detail"]) == 200 and chip["ended_at"]
    assert conn.execute("SELECT COUNT(*) FROM work_steps").fetchone()[0] == 1


def test_the_fields_an_event_moves_are_one_function():
    new = db._order_fields("episode", "01", "started", "r1", "t1", None)
    assert new == {"step_id": "01", "state": "running", "run_id": "r1", "started_at": "t1", "attempts": 1}
    row = {"state": "running", "run_id": "r1", "started_at": "t0", "attempts": 1}
    assert db._order_fields("episode", "02", "started", "r1", "t2", row) == {
        "step_id": "02", "state": "running", "run_id": "r1", "started_at": "t0"}
    assert db._order_fields("episode", "12", "completed", "r1", "t3", row) == {
        "step_id": "12", "state": "done", "finished_at": "t3"}
    assert db._order_fields("episode", "05", "skipped", "r1", "t4", row) == {"step_id": "05"}


def test_the_row_write_is_inside_the_callers_transaction(conn):
    order_id = db._write_work_order(conn, BOOK, "episode", "ep04", None, {"state": "queued"})
    assert db._write_work_order(conn, BOOK, "episode", "ep04", _row(conn), {"step_id": "01"}) == order_id
    conn.rollback()
    assert _row(conn) is None


def test_project_event_is_the_only_writer_and_returns_the_row_id(conn):
    order_id = db.project_event(conn, BOOK, "episode", None, "01", "started", "r1", "t", None)
    assert db.work_order(conn, BOOK, "episode", "book")["id"] == order_id
    assert conn.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 0
