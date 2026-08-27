"""Tests for studio.db — codex master table + events log.

Written FIRST per project rules (CLAUDE.md): no implementation before its test.
No test touches a paid API. All tests run on an in-memory / tmp SQLite DB.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

import pytest

from studio import db


@pytest.fixture()
def conn(tmp_path):
    connection = db.get_connection(tmp_path / "test.db")
    db.init_db(connection)
    yield connection
    connection.close()


# --- schema ---


def test_init_creates_tables(conn):
    names = {
        row["name"]
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }
    assert {"codex", "events"} <= names


def test_init_is_idempotent(conn):
    db.init_db(conn)  # second call must not raise


# --- codex id ---


def test_codex_id_is_14_digit_utc(conn):
    codex_id = db.generate_codex_id()
    assert len(codex_id) == 14
    assert codex_id.isdigit()
    parsed = datetime.strptime(codex_id, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
    delta = abs((parsed - datetime.now(timezone.utc)).total_seconds())
    assert delta < 5  # generated from UTC now


def test_insert_codex_returns_id_and_persists(conn):
    codex_id = db.insert_codex(
        conn,
        "The Way of Kings",
        universe="Cosmere",
        world="Roshar",
        series="Stormlight Archive",
        series_index=1,
        source_type="epub",
        source_ref="books/way_of_kings.epub",
    )
    row = conn.execute("SELECT * FROM codex WHERE id = ?", (codex_id,)).fetchone()
    assert row["name"] == "The Way of Kings"
    assert row["world"] == "Roshar"
    assert row["updated_at"].endswith("Z")


def test_insert_codex_name_required(conn):
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO codex (id, name, updated_at) VALUES ('20260822000000', NULL, 'x')"
        )


def test_insert_codex_collision_retries_plus_one_second(conn, monkeypatch):
    monkeypatch.setattr(db, "generate_codex_id", lambda: "20260822120000")
    first = db.insert_codex(conn, "Book A")
    second = db.insert_codex(conn, "Book B")
    assert first == "20260822120000"
    assert second == "20260822120001"  # +1s on PK conflict, loud not silent


def test_insert_codex_with_explicit_id(conn):
    codex_id = db.insert_codex(conn, "Dracula", codex_id="20260822113400")
    assert codex_id == "20260822113400"
    row = conn.execute("SELECT name FROM codex WHERE id = ?", (codex_id,)).fetchone()
    assert row["name"] == "Dracula"


def test_insert_codex_explicit_id_conflict_is_loud(conn):
    db.insert_codex(conn, "Book A", codex_id="20260822113400")
    with pytest.raises(sqlite3.IntegrityError):
        db.insert_codex(conn, "Book B", codex_id="20260822113400")  # no silent bump


def test_bad_id_length_rejected(conn):
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO codex (id, name, updated_at) VALUES ('123', 'x', 'x')")


def test_bad_source_type_rejected(conn):
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO codex (id, name, source_type, updated_at)"
            " VALUES ('20260822000001', 'x', 'floppy', 'x')"
        )


# --- events ---


def test_add_event_persists(conn):
    codex_id = db.insert_codex(conn, "Dracula", source_type="gutenberg", source_ref="pg345")
    db.add_event(conn, codex_id, "analysis", "01", "started", run_id="run1")
    row = conn.execute("SELECT * FROM events").fetchone()
    assert row["codex_id"] == codex_id
    assert row["stage"] == "analysis"
    assert row["step_id"] == "01"
    assert row["event"] == "started"
    assert row["run_id"] == "run1"
    assert row["event_ts"].endswith("Z")


def test_event_requires_existing_codex(conn):
    with pytest.raises(sqlite3.IntegrityError):
        db.add_event(conn, "19990101000000", "analysis", "01", "started")


def test_event_vocabulary_enforced(conn):
    codex_id = db.insert_codex(conn, "Dracula")
    with pytest.raises(sqlite3.IntegrityError):
        db.add_event(conn, codex_id, "analysis", "01", "exploded")


# --- derived status ---


def test_stage_status_is_latest_event_per_step(conn):
    codex_id = db.insert_codex(conn, "Dracula")
    db.add_event(conn, codex_id, "analysis", "01", "started")
    db.add_event(conn, codex_id, "analysis", "01", "completed")
    db.add_event(conn, codex_id, "analysis", "01_01", "started")
    db.add_event(conn, codex_id, "analysis", "02", "failed")
    status = db.stage_status(conn, codex_id, "analysis")
    assert status == {"01": "completed", "01_01": "started", "02": "failed"}


def test_stage_status_sorted_by_padded_step_id(conn):
    codex_id = db.insert_codex(conn, "Dracula")
    for step in ("02", "01_10", "01", "01_02"):
        db.add_event(conn, codex_id, "analysis", step, "completed")
    status = db.stage_status(conn, codex_id, "analysis")
    assert list(status) == ["01", "01_02", "01_10", "02"]  # text sort = pipeline order


# --- pending scan ---


def test_codex_pending_stage(conn):
    pending = db.insert_codex(conn, "Not Done")
    done = db.insert_codex(conn, "Done")
    db.add_event(conn, done, "analysis", "06", "completed")
    assert db.codex_pending_stage(conn, "analysis", "06") == [pending]


# --- stage summary columns on codex (3 per stage: status, started, updated) ---


def test_codex_has_analysis_stage_columns(conn):
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(codex)")}
    assert {"analysis_status", "analysis_started_at", "analysis_updated_at"} <= cols


def test_migration_adds_columns_to_old_db(tmp_path):
    import sqlite3
    old = sqlite3.connect(tmp_path / "old.db")
    old.execute("CREATE TABLE codex (id TEXT PRIMARY KEY, name TEXT NOT NULL, updated_at TEXT NOT NULL)")
    old.execute("INSERT INTO codex VALUES ('20260101000000', 'Old Book', 'x')")
    old.commit(); old.close()
    conn2 = db.get_connection(tmp_path / "old.db")
    db.init_db(conn2)  # must migrate, not fail
    row = conn2.execute("SELECT analysis_status FROM codex").fetchone()
    assert row["analysis_status"] == "pending"
    conn2.close()


def test_mark_stage_sets_started_once_and_updates(conn):
    codex_id = db.insert_codex(conn, "Dracula")
    db.mark_stage(conn, codex_id, "analysis", "running")
    first = conn.execute("SELECT * FROM codex").fetchone()
    assert first["analysis_status"] == "running"
    assert first["analysis_started_at"] is not None
    db.mark_stage(conn, codex_id, "analysis", "completed")
    second = conn.execute("SELECT * FROM codex").fetchone()
    assert second["analysis_status"] == "completed"
    assert second["analysis_started_at"] == first["analysis_started_at"]  # set once
    assert second["analysis_updated_at"] >= first["analysis_updated_at"]


def test_mark_stage_rejects_unknown_stage(conn):
    codex_id = db.insert_codex(conn, "Dracula")
    with pytest.raises(ValueError):
        db.mark_stage(conn, codex_id, "cooking", "running")


def test_mark_stage_rejects_unknown_status(conn):
    codex_id = db.insert_codex(conn, "Dracula")
    with pytest.raises(ValueError):
        db.mark_stage(conn, codex_id, "analysis", "exploded")


def test_a_batch_of_books_can_be_registered_in_one_second(tmp_path):
    """The codex id is a second-resolution timestamp and collisions bump by +1s. With a
    retry budget of 5 a batch insert died on the seventh book - registering a 22-book
    corpus is not an exotic case, it is Tuesday."""
    conn = db.get_connection(tmp_path / "batch.db")
    db.init_db(conn)
    ids = [db.insert_codex(conn, f"Book {i}") for i in range(30)]
    assert len(set(ids)) == 30


def test_ids_stay_the_documented_width_after_bumping(tmp_path):
    """The codex table CHECKs length(id) = 14; a bump must not change that."""
    conn = db.get_connection(tmp_path / "w.db")
    db.init_db(conn)
    assert all(len(db.insert_codex(conn, f"B{i}")) == 14 for i in range(20))


def test_an_explicit_id_still_refuses_to_bump(tmp_path):
    """An explicit id matches an existing library folder. Bumping it would silently
    point at the wrong book."""
    import sqlite3
    import pytest
    conn = db.get_connection(tmp_path / "e.db")
    db.init_db(conn)
    db.insert_codex(conn, "First", codex_id="20260827000001")
    with pytest.raises(sqlite3.IntegrityError):
        db.insert_codex(conn, "Second", codex_id="20260827000001")
