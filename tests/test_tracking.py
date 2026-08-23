"""Tests for studio.tracking — standardized events + JSONL run logs for all stages."""

from __future__ import annotations

import json

import pytest

from studio import db, tracking


@pytest.fixture()
def conn(tmp_path):
    connection = db.get_connection(tmp_path / "test.db")
    db.init_db(connection)
    yield connection
    connection.close()


@pytest.fixture()
def tracker(conn, tmp_path):
    codex_id = db.insert_codex(conn, "Dracula")
    return tracking.Tracker(conn, codex_id, "analysis", logs_root=tmp_path / "logs")


# --- run id ---


def test_make_run_id_format():
    run_id = tracking.make_run_id("20260822113400", "analysis")
    prefix, stage, ts = run_id.split("__")
    assert prefix == "20260822113400"
    assert stage == "analysis"
    assert ts.isdigit() and len(ts) == 14


# --- step context: events ---


def test_step_success_emits_started_and_completed(tracker):
    with tracker.step("01_01"):
        pass
    events = [r["event"] for r in tracker.conn.execute(
        "SELECT event FROM events WHERE step_id='01_01' ORDER BY event_ts")]
    assert events == ["started", "completed"]


def test_step_failure_emits_failed_and_reraises(tracker):
    with pytest.raises(ValueError):
        with tracker.step("01_02"):
            raise ValueError("boom with details")
    row = tracker.conn.execute(
        "SELECT event, detail FROM events WHERE step_id='01_02'"
        " ORDER BY event_ts DESC").fetchone()
    assert row["event"] == "failed"
    assert "boom" in row["detail"]  # one-line summary lands in detail


def test_events_carry_run_id(tracker):
    with tracker.step("01_01"):
        pass
    row = tracker.conn.execute("SELECT run_id FROM events LIMIT 1").fetchone()
    assert row["run_id"] == tracker.run_id


# --- logs: JSONL file per run ---


def test_log_writes_jsonl_with_context(tracker):
    tracker.log("hello world", step_id="01_01")
    lines = [json.loads(line) for line in tracker.log_path.read_text().splitlines()]
    assert lines[-1]["msg"] == "hello world"
    assert lines[-1]["step_id"] == "01_01"
    assert lines[-1]["stage"] == "analysis"
    assert lines[-1]["level"] == "INFO"


def test_step_failure_logs_traceback(tracker):
    with pytest.raises(RuntimeError):
        with tracker.step("01_03"):
            raise RuntimeError("kaput")
    text = tracker.log_path.read_text()
    assert "kaput" in text and "Traceback" in text  # full trace in log, not in events


def test_log_path_layout(tracker):
    tracker.log("x")
    assert tracker.log_path.parent.name == "analysis"
    assert tracker.log_path.parent.parent.name == tracker.codex_id
    assert tracker.log_path.name == f"{tracker.run_id}.log"


# --- codex updates ---


def test_update_codex_sets_fields_and_timestamp(conn):
    codex_id = db.insert_codex(conn, "Dracula")
    before = conn.execute("SELECT updated_at FROM codex").fetchone()["updated_at"]
    db.update_codex(conn, codex_id, world="Transylvania", series="Dracula")
    row = conn.execute("SELECT * FROM codex WHERE id=?", (codex_id,)).fetchone()
    assert row["world"] == "Transylvania"
    assert row["updated_at"] >= before


def test_update_codex_rejects_unknown_column(conn):
    codex_id = db.insert_codex(conn, "Dracula")
    with pytest.raises(ValueError):
        db.update_codex(conn, codex_id, hacker_field="x")


def test_update_codex_rejects_unknown_id(conn):
    with pytest.raises(ValueError):
        db.update_codex(conn, "19990101000000", name="ghost")
