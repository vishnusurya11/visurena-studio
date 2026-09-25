"""A unit whose plan the battery never let through is DEFERRED: the step says
so, the runner records `deferred`, prints the line and stops the unit -- no
later step runs on a plan that does not exist.  Episode 13's first run
deferred at step 02 and then launched step 03 on the missing plan.json."""
from __future__ import annotations

import sqlite3

import pytest

from studio import db, step_runner
from studio.deferral import Deferred
from tests.test_step_runner import _ctx, _step, conn  # noqa: F401


def test_the_line_names_the_gate_the_unit_and_where_the_draft_went():
    d = Deferred("PLAN", "episodes/ep13/plan.deferred.json", "battery at plan -> defer")
    assert d.line("20260901000001 episode/ep13") == (
        "DEFERRED PLAN | 20260901000001 episode/ep13 | battery at plan -> defer"
        " | aside: episodes/ep13/plan.deferred.json")


def test_a_deferral_stops_the_unit_and_is_an_event(conn, tmp_path, capsys):
    ctx = _ctx(conn, tmp_path)
    ran = []

    def defer(c):
        raise Deferred("PLAN", "episodes/ep01/plan.deferred.json", "battery at plan -> defer")

    steps = [_step("02", defer), _step("03", lambda c: ran.append("03"))]
    assert step_runner.run_steps(ctx, steps) == "deferred"
    assert ran == []
    assert db.unit_status(conn, ctx.codex_id, "episode", "ep01") == {"02": "deferred"}
    row = conn.execute("SELECT detail FROM events WHERE event = 'deferred'").fetchone()
    assert "PLAN" in row["detail"] and "plan.deferred.json" in row["detail"]
    assert "DEFERRED PLAN" in capsys.readouterr().out


def test_deferred_is_in_the_vocabulary_and_an_old_table_is_brought_forward(tmp_path):
    assert "deferred" in db.EVENT_VOCABULARY
    conn = sqlite3.connect(tmp_path / "old.db")
    conn.row_factory = sqlite3.Row
    old = db._events_ddl().replace(", 'deferred'", "")
    assert "deferred" not in old
    conn.executescript(db._DDL[:db._DDL.index("CREATE TABLE IF NOT EXISTS events")] + old)
    db.init_db(conn)
    codex_id = db.insert_codex(conn, "Book", codex_id="20260901000001")
    db.add_event(conn, codex_id, "episode", "02", "deferred", unit="ep01", detail="PLAN")
    assert db.unit_status(conn, codex_id, "episode", "ep01")["02"] == "deferred"


def test_an_event_outside_the_vocabulary_is_still_refused(conn):
    codex_id = db.insert_codex(conn, "Book", codex_id="20260901000002")
    with pytest.raises(sqlite3.IntegrityError):
        db.add_event(conn, codex_id, "episode", "02", "parked", unit="ep01")
