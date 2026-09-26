"""A book-level department that declares no outputs yet (analysis, screenplay,
trailer) cannot settle from disk; the ledger already knows it finished --
runners write codex.<stage>_status = 'completed'.  First live tick,
2026-09-26: 30 analyses read `queued` although most were done years of
GPU-hours ago."""
from __future__ import annotations

from studio import db
from studio import tick


def _conn(tmp_path):
    conn = db.get_connection(tmp_path / "t.db")
    db.init_db(conn)
    return conn


def test_a_completed_book_stage_settles_done(tmp_path):
    conn = _conn(tmp_path)
    codex = db.insert_codex(conn, "Book", codex_id="20260901000001")
    tick.materialize(conn, codex, "analysis", ["book"])
    db.mark_stage(conn, codex, "analysis", "completed")
    assert tick.settle_from_ledger(conn, codex, "analysis", "book") is True
    assert db.work_order(conn, codex, "analysis", "book")["state"] == "done"


def test_a_pending_book_stage_and_a_unit_stage_are_left_alone(tmp_path):
    conn = _conn(tmp_path)
    codex = db.insert_codex(conn, "Book", codex_id="20260901000001")
    tick.materialize(conn, codex, "analysis", ["book"])
    assert tick.settle_from_ledger(conn, codex, "analysis", "book") is False
    tick.materialize(conn, codex, "episode", ["ep01"])
    db.mark_stage(conn, codex, "episode", "completed")
    assert tick.settle_from_ledger(conn, codex, "episode", "ep01") is False
    assert db.work_order(conn, codex, "episode", "ep01")["state"] == "blocked"
