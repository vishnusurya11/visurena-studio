"""A full run of a unit -- started/completed over every registered step -- leaves
ONE row in its department's table (decision 2026-09-25, the Command Center): the
row is `done` on the stage's last step, with finished_at set, and one work_steps
chip per step, every one `done`.  No runner wrote it: add_event did, one place."""
from __future__ import annotations

import pytest

from studio import db, registry

BOOK = "20260901000001"


@pytest.fixture()
def conn(tmp_path):
    connection = db.get_connection(tmp_path / "t.db")
    db.init_db(connection)
    db.insert_codex(connection, "Book", codex_id=BOOK)
    return connection


def _run_every_step(conn, run_id="r1"):
    for entry in registry.steps("episode"):
        db.add_event(conn, BOOK, "episode", entry["id"], "started", run_id=run_id, unit="ep03")
        db.add_event(conn, BOOK, "episode", entry["id"], "completed", run_id=run_id, unit="ep03")


def test_a_finished_unit_is_one_done_row(conn):
    _run_every_step(conn)
    rows = list(conn.execute("SELECT * FROM episode_orders"))
    assert len(rows) == 1
    row = rows[0]
    assert (row["unit"], row["state"], row["step_id"]) == ("ep03", "done", "12")
    assert row["step_id"] == registry.steps("episode")[-1]["id"]
    assert row["finished_at"] and row["started_at"] and row["run_id"] == "r1"
    assert row["attempts"] == 1


def test_one_work_steps_chip_per_step_all_done(conn):
    _run_every_step(conn)
    order_id = db.work_order(conn, BOOK, "episode", "ep03")["id"]
    chips = list(conn.execute(
        "SELECT * FROM work_steps WHERE order_id = ? ORDER BY step_id", (order_id,)))
    assert [c["step_id"] for c in chips] == [e["id"] for e in registry.steps("episode")]
    assert {c["state"] for c in chips} == {"done"}
    assert {c["attempt"] for c in chips} == {1}
    assert all(c["started_at"] and c["ended_at"] and c["run_id"] == "r1" for c in chips)


def test_a_completed_middle_step_keeps_the_unit_running_and_advances_the_step(conn):
    db.add_event(conn, BOOK, "episode", "01", "started", run_id="r1", unit="ep03")
    db.add_event(conn, BOOK, "episode", "01", "completed", run_id="r1", unit="ep03")
    row = db.work_order(conn, BOOK, "episode", "ep03")
    assert (row["state"], row["step_id"], row["finished_at"]) == ("running", "01", None)


def test_only_the_stages_last_step_finishes_the_unit():
    last = registry.steps("episode")[-1]["id"]
    assert db._order_state("episode", last, "completed") == "done"
    assert db._order_state("episode", "01", "completed") == "running"
    assert db._order_state("refs", registry.steps("refs")[-1]["id"], "completed") == "done"
    assert db._final_step_id("episode") == "12"
    assert db._final_step_id("no-such-stage") is None
