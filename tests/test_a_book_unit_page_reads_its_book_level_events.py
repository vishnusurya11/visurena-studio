"""Board review 2026-10-12 (02 #9): the analysis, screenplay and trailer unit
pages said "no runs yet" / "finished in 0 runs" over hundreds of events.  A
book-level runner writes `unit` NULL (db.add_event); the page asked for
`unit = 'book'`.  pulse.unit_row already reads NULL as `book`.  $0."""
from __future__ import annotations

from studio import db
from studio.command_center import unit_view

CODEX = "20990101000000"


def _conn(tmp_path):
    conn = db.get_connection(tmp_path / "t.db")
    db.init_db(conn)
    db.insert_codex(conn, "A Book", codex_id=CODEX)
    return conn


def test_a_null_unit_event_belongs_to_the_book_unit(tmp_path):
    conn = _conn(tmp_path)
    db.add_event(conn, CODEX, "screenplay", "01", "started", run_id="r1")
    db.add_event(conn, CODEX, "screenplay", "01", "completed", run_id="r1")
    events = unit_view.unit_events(conn, CODEX, "screenplay", "book")
    assert [e["event"] for e in events] == ["started", "completed"]


def test_an_episode_still_reads_only_its_own_events(tmp_path):
    conn = _conn(tmp_path)
    db.add_event(conn, CODEX, "episode", "01", "started", run_id="r1", unit="ep01")
    db.add_event(conn, CODEX, "episode", "01", "started", run_id="r2", unit="ep02")
    assert [e["run_id"] for e in unit_view.unit_events(conn, CODEX, "episode", "ep01")] == ["r1"]
    assert unit_view.unit_events(conn, CODEX, "episode", "book") == []
