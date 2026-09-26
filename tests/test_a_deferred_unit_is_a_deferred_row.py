"""A judge's terminal sets a unit aside: the `deferred` event makes the unit's
row `deferred` at the step that deferred it, and the chip carries the line.  The
row waits (decision 2026-09-25) until a later run starts it again -- then it is
`running` and that run is a second pass."""
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


def test_a_deferred_unit_is_a_deferred_row_at_its_step(conn):
    db.add_event(conn, BOOK, "episode", "02", "started", run_id="r1", unit="ep13")
    db.add_event(conn, BOOK, "episode", "02", "deferred", run_id="r1", unit="ep13",
                 detail="DEFERRED PLAN | battery at plan -> defer")
    row = db.work_order(conn, BOOK, "episode", "ep13")
    assert (row["state"], row["step_id"], row["attempts"]) == ("deferred", "02", 1)
    assert row["finished_at"] is None
    assert [r["state"] for r in conn.execute("SELECT state FROM v_attention")] == ["deferred"]


def test_the_chip_carries_the_deferral_line(conn):
    db.add_event(conn, BOOK, "episode", "02", "started", run_id="r1", unit="ep13")
    db.add_event(conn, BOOK, "episode", "02", "deferred", run_id="r1", unit="ep13",
                 detail="DEFERRED PLAN | battery at plan -> defer")
    chip = conn.execute("SELECT * FROM work_steps").fetchone()
    assert (chip["step_id"], chip["state"], chip["attempt"]) == ("02", "deferred", 1)
    assert chip["started_at"] and chip["ended_at"] and "PLAN" in chip["detail"]


def test_a_later_started_makes_the_unit_running_again_as_a_second_pass(conn):
    db.add_event(conn, BOOK, "episode", "02", "started", run_id="r1", unit="ep13")
    db.add_event(conn, BOOK, "episode", "02", "deferred", run_id="r1", unit="ep13")
    db.add_event(conn, BOOK, "episode", "02", "started", run_id="r2", unit="ep13")
    row = db.work_order(conn, BOOK, "episode", "ep13")
    assert (row["state"], row["step_id"], row["run_id"], row["attempts"]) == ("running", "02", "r2", 2)
    chip = conn.execute("SELECT * FROM work_steps").fetchone()
    assert (chip["state"], chip["attempt"], chip["run_id"], chip["ended_at"]) == ("running", 2, "r2", None)
    assert conn.execute("SELECT COUNT(*) FROM work_orders").fetchone()[0] == 1
