"""C8: a live run owns its row.  A work-order row that is `running` under a
run_id is skipped by the plan and never written, force or not; a row whose run
ended (failed, done) is re-derived from disk with source='backfill'.  A DB
that has not been migrated (no work_orders table, the live one opened
read-only) answers "no row" instead of failing the dry run."""
from __future__ import annotations

import sqlite3

import pytest

from studio import backfill, db, episode_home

CODEX = "20260901000001"


@pytest.fixture()
def library(tmp_path, monkeypatch):
    folder = tmp_path / "library"
    folder.mkdir()
    monkeypatch.setattr(episode_home, "LIBRARY", folder)
    return folder


@pytest.fixture()
def book(library):
    folder = library / f"{CODEX}_a-book"
    folder.mkdir()
    return folder


@pytest.fixture()
def conn(tmp_path):
    connection = db.get_connection(tmp_path / "t.db")
    db.init_db(connection)
    db.insert_codex(connection, "Book", codex_id=CODEX)
    return connection


def _done_on_disk(book, unit="ep04"):
    home = book / "episodes" / unit
    episode_home.write_json(home / "plan.json", {"number": 4})
    (home / "cut").mkdir(parents=True)
    (home / "cut" / "master_r2v.mp4").write_bytes(b"m")
    episode_home.write_json(home / "qc_r2v.json", {"passed": True})


def test_a_running_row_is_skipped_and_never_written(book, conn, library):
    _done_on_disk(book)
    db.add_event(conn, CODEX, "episode", "09", "started", run_id="r1", unit="ep04")
    entries = backfill.plan(conn, library)
    assert entries[0]["live_run"] == "r1" and entries[0]["existing_state"] == "running"
    assert backfill.write(conn, entries) == 0 and backfill.write(conn, entries, force=True) == 0
    row = db.work_order(conn, CODEX, "episode", "ep04")
    assert row["state"] == "running" and row["source"] == "run" and row["run_id"] == "r1"


def test_a_row_whose_run_ended_is_re_derived_from_disk(book, conn, library):
    _done_on_disk(book)
    db.add_event(conn, CODEX, "episode", "09", "started", run_id="r1", unit="ep04")
    db.add_event(conn, CODEX, "episode", "09", "failed", run_id="r1", unit="ep04")
    entries = backfill.plan(conn, library)
    assert entries[0]["live_run"] is None and entries[0]["existing_state"] == "failed"
    assert backfill.write(conn, entries) == 1
    row = db.work_order(conn, CODEX, "episode", "ep04")
    assert row["state"] == "done" and row["source"] == "backfill" and row["attempts"] == 1
    assert row["run_id"] == "r1" and row["deliverable"] == "episodes/ep04/cut/master_r2v.mp4"


def test_live_run_of_reads_only_a_running_row_with_a_run_id():
    class Row(dict):
        __getitem__ = dict.get
    assert backfill.live_run_of(None) is None
    assert backfill.live_run_of(Row(state="running", run_id="r1")) == "r1"
    assert backfill.live_run_of(Row(state="running", run_id=None)) is None
    assert backfill.live_run_of(Row(state="done", run_id="r1")) is None


def test_a_db_without_the_table_answers_no_row(tmp_path, book, library):
    bare = sqlite3.connect(tmp_path / "old.db")
    bare.row_factory = sqlite3.Row
    bare.executescript(db._DDL)
    assert backfill.existing_row(bare, CODEX, "episode", "ep04") is None
    _done_on_disk(book)
    entries = backfill.plan(bare, library)
    assert len(entries) == 1 and entries[0]["existing_state"] is None


def test_writable_is_the_one_rule_write_follows():
    assert backfill.writable({"live_run": None, "ambiguous": None}, False)
    assert not backfill.writable({"live_run": None, "ambiguous": "x"}, False)
    assert backfill.writable({"live_run": None, "ambiguous": "x"}, True)
    assert not backfill.writable({"live_run": "r1", "ambiguous": None}, True)


def test_books_of_takes_codex_folders_and_filters_by_id(library):
    (library / f"{CODEX}_a-book").mkdir()
    (library / "20260901000002_b-book").mkdir()
    (library / "_scopes").mkdir()
    assert [c for c, _ in backfill.books_of(library)] == [CODEX, "20260901000002"]
    assert [c for c, _ in backfill.books_of(library, ["20260901000002"])] == ["20260901000002"]
