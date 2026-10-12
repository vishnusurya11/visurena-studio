"""Board review 2026-10-12 (02 #1, #2, #3): the board only knew what a runner wrote
into work_orders, so all 30 screenplays and trailers read `queued, step – of N`
over hundreds of events, Dracula/P&P/Dubliners/Jekyll screenplays that FAILED
were not in Needs you, and Scarlet's legacy refs (consumed by 14 published
episodes) sat first in the queue forever.

The rule (decision 2026-10-12_the_ledger_settles_book_stages):
- a book-level row the ledger has terminal events for is what the ledger says:
  done when the last step completed (flagged when a later re-run failed),
  failed when its newest terminal event failed, else its cursor moves to the
  step after the newest one completed;
- the disk (`deliverable:`) settles only a row the ledger is silent on;
- an upstream row with no ledger and no deliverable, whose consumer has a
  published unit, is done as consumed.  $0."""
from __future__ import annotations

import json

import pytest

from studio import db, episode_home, ledger_settle, registry, tick

CODEX = "20990101000000"


@pytest.fixture()
def conn(tmp_path):
    connection = db.get_connection(tmp_path / "t.db")
    db.init_db(connection)
    db.insert_codex(connection, "A Book", codex_id=CODEX)
    return connection


@pytest.fixture()
def book(tmp_path):
    folder = tmp_path / "library" / f"{CODEX}_a-book"
    folder.mkdir(parents=True)
    return folder


def _ev(conn, stage, step, event, detail=None, unit=None):
    db.add_event(conn, CODEX, stage, step, event, run_id="r", detail=detail, unit=unit)


def _queued(conn, stage, unit="book"):
    db.upsert_work_order(conn, CODEX, stage, unit, state="queued", step_id=None, source="queue")


def _e(i, step, event, detail=None):
    return {"id": i, "event_ts": f"2026-09-0{i}T00:00:00Z", "step_id": step, "event": event, "detail": detail}


# --- the reading: pure ---


def test_the_last_step_completed_reads_done():
    got = ledger_settle.reading([_e(1, "04", "completed"), _e(2, "05", "completed")], "05", "screenplay")
    assert (got["state"], got["step_id"], got["flags"]) == ("done", "05", 0)


def test_a_rerun_that_failed_after_the_delivery_is_a_flag():
    got = ledger_settle.reading([_e(1, "10", "completed"), _e(2, "03", "failed", "Value error, beats")], "10", "trailer")
    assert (got["state"], got["flags"]) == ("done", 1) and "re-run failed at 03" in got["note"]


def test_a_newest_failure_with_no_delivery_reads_failed():
    got = ledger_settle.reading([_e(1, "01", "completed"), _e(2, "02", "failed", "plan checks failed: 2")], "05",
                                "screenplay")
    assert (got["state"], got["step_id"]) == ("failed", "02") and "plan checks failed" in got["note"]


def test_completed_steps_move_the_cursor_only():
    got = ledger_settle.reading([_e(1, "03", "completed"), _e(2, "04", "completed")], "05", "screenplay")
    assert got["state"] is None and got["step_id"] == "05"


def test_no_terminal_event_is_no_reading():
    assert ledger_settle.reading([], "05", "screenplay") is None


def test_the_next_step_follows_the_registry():
    assert ledger_settle.next_step("screenplay", "04") == "05"
    assert ledger_settle.next_step("screenplay", "05") == "05"


# --- the tick ---


def test_a_failed_screenplay_is_failed_and_needs_you(conn, book):
    """The August events predate the rows: materialize (09-26) wrote them queued after."""
    _ev(conn, "screenplay", "01", "completed")
    _ev(conn, "screenplay", "02", "failed", detail="plan checks failed: 2; first: 16 beats")
    _ev(conn, "screenplay", "02_03", "failed", detail="substep")
    _queued(conn, "screenplay")
    assert tick.settle_from_events(conn, CODEX, "screenplay", "book") == "settled"
    row = db.work_order(conn, CODEX, "screenplay", "book")
    assert (row["state"], row["step_id"]) == ("failed", "02") and "16 beats" in row["note"]


def test_the_ledger_beats_a_qc_report_from_a_failed_verify(conn, book):
    episode_home.write_json(book / "screenplay" / "feature" / "qc_report.json", {"blocking": 56})
    _ev(conn, "screenplay", "05", "failed", detail="56 blocking finding(s)")
    _queued(conn, "screenplay")
    tick.tick_unit(conn, CODEX, "screenplay", "book", book)
    assert db.work_order(conn, CODEX, "screenplay", "book")["state"] == "failed"


def test_a_screenplay_at_04_stays_queued_with_its_cursor_at_05(conn, book):
    db.upsert_work_order(conn, CODEX, "analysis", "book", state="done")
    _queued(conn, "screenplay")
    for step in ("01", "02", "03", "04"):
        _ev(conn, "screenplay", step, "completed")
    db.upsert_work_order(conn, CODEX, "screenplay", "book", state="queued")
    assert tick.settle_from_events(conn, CODEX, "screenplay", "book") == "cursor"
    row = db.work_order(conn, CODEX, "screenplay", "book")
    assert (row["state"], row["step_id"]) == ("queued", "05")


def test_a_trailer_with_no_ledger_settles_from_its_file(conn, book):
    _queued(conn, "trailer")
    (book / "trailer" / "main").mkdir(parents=True)
    (book / "trailer" / "main" / "TRAILER-a-book.mp4").write_bytes(b"mp4")
    tick.tick_unit(conn, CODEX, "trailer", "book", book)
    row = db.work_order(conn, CODEX, "trailer", "book")
    assert row["state"] == "done" and row["deliverable"] == "trailer/main/TRAILER-a-book.mp4"


def test_legacy_refs_consumed_by_a_published_episode_are_done(conn, book):
    db.upsert_work_order(conn, CODEX, "refs", "main", state="queued", step_id="03", source="backfill")
    episode_home.write_json(book / "episodes" / "ep01" / "youtube.json", {})
    (book / "uploads.jsonl").write_text(json.dumps({"episode": 1, "video_id": "v", "sha8": "abcd1234"}) + "\n",
                                        encoding="utf-8")
    assert tick.settle_consumed(conn, CODEX, "refs", "main", book) is True
    row = db.work_order(conn, CODEX, "refs", "main")
    assert row["state"] == "done" and "consumed by 1 published" in row["note"]


def test_refs_with_no_published_consumer_stay_where_they_are(conn, book):
    db.upsert_work_order(conn, CODEX, "refs", "main", state="queued", source="queue")
    assert tick.settle_consumed(conn, CODEX, "refs", "main", book) is False
    assert db.work_order(conn, CODEX, "refs", "main")["state"] == "queued"


def test_a_running_row_is_never_settled_by_the_ledger(conn, book):
    _ev(conn, "refs", "01", "failed", unit="main")
    db.upsert_work_order(conn, CODEX, "refs", "main", state="running", step_id="02")
    assert tick.settle_from_events(conn, CODEX, "refs", "main") == ""
    assert db.work_order(conn, CODEX, "refs", "main")["state"] == "running"


def test_every_book_stage_declares_its_deliverable():
    assert registry.deliverable_of("analysis") == "analysis/qc_report.json"
    assert registry.deliverable_of("screenplay") == "screenplay/feature/qc_report.json"
    assert registry.deliverable_of("trailer") == "trailer/main/TRAILER-*.mp4"
