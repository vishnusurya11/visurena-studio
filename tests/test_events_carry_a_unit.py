"""A stage that fans out below the book (one chapter per episode) needs its events
to say WHICH unit they are about, or two episodes of one book would read as one
step run twice.  The column is opaque text; each stage declares its grammar.

An old library.db has no such column and refuses `escalated`; init_db must bring
both in without losing a row."""
from __future__ import annotations

import pytest

from studio import db

OLD_DDL = """
CREATE TABLE codex (id TEXT PRIMARY KEY CHECK (length(id) = 14), name TEXT NOT NULL,
  universe TEXT, world TEXT, series TEXT, series_index INTEGER, source_type TEXT,
  source_ref TEXT, updated_at TEXT NOT NULL);
CREATE TABLE events (id INTEGER PRIMARY KEY, event_ts TEXT NOT NULL,
  codex_id TEXT NOT NULL REFERENCES codex(id), stage TEXT NOT NULL, step_id TEXT NOT NULL,
  event TEXT NOT NULL CHECK (event IN ('started', 'completed', 'failed', 'skipped')),
  run_id TEXT, detail TEXT);
"""


@pytest.fixture()
def conn(tmp_path):
    connection = db.get_connection(tmp_path / "t.db")
    db.init_db(connection)
    return connection


def _book(conn, codex_id="20260901000001"):
    return db.insert_codex(conn, "Book", codex_id=codex_id)


def test_two_units_of_one_stage_do_not_collide(conn):
    codex_id = _book(conn)
    db.add_event(conn, codex_id, "episode", "04", "completed", unit="ep01")
    db.add_event(conn, codex_id, "episode", "04", "started", unit="ep02")
    assert db.unit_status(conn, codex_id, "episode", "ep01")["04"] == "completed"
    assert db.unit_status(conn, codex_id, "episode", "ep02")["04"] == "started"
    assert db.unit_status(conn, codex_id, "episode", "ep03") == {}


def test_a_book_level_stage_leaves_the_unit_null(conn):
    codex_id = _book(conn)
    db.add_event(conn, codex_id, "analysis", "01", "completed")
    row = conn.execute("SELECT unit FROM events").fetchone()
    assert row["unit"] is None


def test_escalated_is_an_event(conn):
    codex_id = _book(conn)
    db.add_event(conn, codex_id, "episode", "02", "escalated", unit="ep01", detail="PLAN")
    assert db.unit_status(conn, codex_id, "episode", "ep01")["02"] == "escalated"


def test_the_registry_decides_which_stages_the_codex_table_knows(conn):
    codex_id = _book(conn)
    db.mark_stage(conn, codex_id, "episode", "running")
    assert db.get_codex(conn, codex_id)["episode_status"] == "running"
    with pytest.raises(ValueError):
        db.mark_stage(conn, codex_id, "bogus", "running")


def test_init_db_brings_an_old_db_forward_without_losing_a_row(tmp_path):
    old = db.get_connection(tmp_path / "old.db")
    old.executescript(OLD_DDL)
    old.execute("INSERT INTO codex (id, name, updated_at) VALUES ('20260901000001', 'B', 'x')")
    old.execute("INSERT INTO events (event_ts, codex_id, stage, step_id, event)"
                " VALUES ('t', '20260901000001', 'analysis', '01', 'completed')")
    old.commit()
    db.init_db(old)
    cols = {row["name"] for row in old.execute("PRAGMA table_info(events)")}
    assert "unit" in cols
    assert old.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 1
    db.add_event(old, "20260901000001", "episode", "02", "escalated", unit="ep01")
    assert old.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 2
