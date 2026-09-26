"""studio/queue.py -- the pull (decision 2026-09-25, "How a department is
driven", "The GPU", "Explicit invocation").  A runner reads its department's
queue in v_queue order, claims a queued row under its run (claimed_by, a
15-minute lease, run_id), renews the lease with every event it writes,
releases the claim when the run ends, and the explicit form gets a word on
its own row.  Nothing here runs a step or reads the disk."""
from __future__ import annotations

import sqlite3
import types
from datetime import datetime, timedelta, timezone

import pytest

from studio import db, queue, step_runner, tick, tracking, work_orders

CODEX = "20260901000001"
OTHER = "20260901000002"


@pytest.fixture()
def conn(tmp_path):
    connection = db.get_connection(tmp_path / "t.db")
    db.init_db(connection)
    db.insert_codex(connection, "Book", codex_id=CODEX)
    db.insert_codex(connection, "Other", codex_id=OTHER)
    return connection


@pytest.fixture()
def cpu_stage(monkeypatch):
    """Every stage's steps are CPU steps: the GPU index stays out of the way."""
    monkeypatch.setattr(queue, "stage_uses_gpu", lambda stage: False)


def _row(conn, unit, stage="episode", codex=CODEX):
    return db.work_order(conn, codex, stage, unit)


def _parse(ts: str) -> datetime:
    return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def _order(conn, unit, state, priority=0, sequence=None, **fields):
    return db.upsert_work_order(conn, CODEX, "episode", unit, state=state, priority=priority,
                                sequence=sequence or int(unit[2:]), **fields)


# --- reading the queue ---


def test_queued_units_are_one_books_department_in_priority_sequence_unit_order(conn):
    _order(conn, "ep05", "queued", priority=1)
    _order(conn, "ep03", "queued", priority=0)
    _order(conn, "ep04", "queued", priority=0)
    _order(conn, "ep02", "blocked")
    _order(conn, "ep06", "deferred")
    _order(conn, "ep07", "held")
    db.upsert_work_order(conn, CODEX, "refs", "main", state="queued")
    db.upsert_work_order(conn, OTHER, "episode", "ep01", state="queued")
    assert queue.queued_units(conn, CODEX, "episode") == ["ep03", "ep04", "ep05"]
    assert queue.queued_units(conn, CODEX, "trailer") == []


def test_queued_books_are_the_books_whose_row_is_queued_and_has_rows_says_if_any(conn):
    assert queue.has_rows(conn, "refs") is False
    assert queue.queued_books(conn, "refs", "main") == []
    db.upsert_work_order(conn, OTHER, "refs", "main", state="queued", priority=0)
    db.upsert_work_order(conn, CODEX, "refs", "main", state="queued", priority=1)
    assert queue.has_rows(conn, "refs") is True
    assert queue.queued_books(conn, "refs", "main") == [OTHER, CODEX]
    db.upsert_work_order(conn, CODEX, "refs", "main", state="done")
    assert queue.queued_books(conn, "refs", "main") == [OTHER]


# --- the claim ---


def test_lease_until_is_utc_seconds_ahead_and_claimant_names_host_and_pid():
    until = _parse(queue.lease_until(900))
    now = datetime.now(timezone.utc)
    assert timedelta(seconds=890) < until - now < timedelta(seconds=910)
    host, pid = queue.claimant().rsplit(":", 1)
    assert host and pid.isdigit()


def test_stage_uses_gpu_reads_the_step_modules(monkeypatch):
    monkeypatch.setattr(step_runner, "load_steps",
                        lambda stage: [types.SimpleNamespace(GPU=stage == "gpu-line")])
    assert queue.stage_uses_gpu("gpu-line") is True
    assert queue.stage_uses_gpu("cpu-line") is False


def test_claim_takes_a_queued_row_under_the_run_once(conn, cpu_stage):
    _order(conn, "ep04", "queued")
    assert queue.claim(conn, CODEX, "episode", "ep04", "run-1") is True
    row = _row(conn, "ep04")
    assert (row["state"], row["run_id"]) == ("running", "run-1")
    assert row["claimed_by"] == queue.claimant()
    assert timedelta(seconds=880) < _parse(row["lease_until"]) - datetime.now(timezone.utc)
    assert queue.claim(conn, CODEX, "episode", "ep04", "run-2") is False
    assert _row(conn, "ep04")["run_id"] == "run-1"


def test_claim_refuses_a_row_that_is_not_queued(conn, cpu_stage):
    for unit, state in (("ep01", "blocked"), ("ep02", "deferred"), ("ep03", "held"), ("ep05", "done")):
        _order(conn, unit, state)
        assert queue.claim(conn, CODEX, "episode", unit, "run-1") is False
        assert (_row(conn, unit)["state"], _row(conn, unit)["claimed_by"]) == (state, None)
    assert queue.claim(conn, CODEX, "episode", "ep09", "run-1") is False


def test_a_gpu_claim_beside_a_running_gpu_row_is_refused_by_the_index_not_an_error(conn, monkeypatch):
    monkeypatch.setattr(queue, "stage_uses_gpu", lambda stage: True)
    first = _order(conn, "ep04", "queued")
    db.claim_gpu(conn, first)
    _order(conn, "ep05", "queued")
    assert queue.claim(conn, CODEX, "episode", "ep05", "run-2") is False
    row = _row(conn, "ep05")
    assert (row["state"], row["claimed_by"], row["gpu"]) == ("queued", None, 0)
    conn.execute("SELECT 1")  # the connection is usable: the failed statement was rolled back


def test_a_gpu_stage_claim_marks_the_row_gpu(conn, monkeypatch):
    monkeypatch.setattr(queue, "stage_uses_gpu", lambda stage: True)
    _order(conn, "ep04", "queued")
    assert queue.claim(conn, CODEX, "episode", "ep04", "run-1") is True
    assert _row(conn, "ep04")["gpu"] == 1


# --- the lease ---


def test_renew_pushes_a_running_rows_lease_forward_and_leaves_every_other_row(conn, cpu_stage):
    _order(conn, "ep04", "queued")
    queue.claim(conn, CODEX, "episode", "ep04", "run-1")
    db.upsert_work_order(conn, CODEX, "episode", "ep04", lease_until="2020-01-01T00:00:00Z")
    assert queue.renew(conn, CODEX, "episode", "ep04") is True
    assert _parse(_row(conn, "ep04")["lease_until"]) > datetime.now(timezone.utc)
    _order(conn, "ep05", "done", lease_until="2020-01-01T00:00:00Z")
    assert queue.renew(conn, CODEX, "episode", "ep05") is False
    assert _row(conn, "ep05")["lease_until"] == "2020-01-01T00:00:00Z"
    assert queue.renew(conn, CODEX, "episode", "ep09") is False


def test_the_tracker_renews_the_lease_with_every_event_it_writes(conn, tmp_path, monkeypatch, cpu_stage):
    monkeypatch.setattr(tick, "tick_book", lambda conn, codex_id: None)
    _order(conn, "ep04", "queued")
    tracker = tracking.Tracker(conn, CODEX, "episode", logs_root=tmp_path / "logs", unit="ep04")
    queue.claim(conn, CODEX, "episode", "ep04", tracker.run_id)
    db.upsert_work_order(conn, CODEX, "episode", "ep04", lease_until="2020-01-01T00:00:00Z")
    tracker.event("03", "started")
    assert _parse(_row(conn, "ep04")["lease_until"]) > datetime.now(timezone.utc)
    tracker.event("03", "completed")
    assert _row(conn, "ep04")["state"] == "running"
    # a unit with no row (a book never ticked, a book-level stage) is a no-op
    tracking.Tracker(conn, OTHER, "analysis", logs_root=tmp_path / "logs").event("01", "started")
    assert db.work_order(conn, OTHER, "analysis", "book")["lease_until"] is not None


# --- the release ---


def test_release_clears_the_claim_of_a_settled_row(conn, cpu_stage):
    _order(conn, "ep04", "queued")
    queue.claim(conn, CODEX, "episode", "ep04", "run-1")
    db.add_event(conn, CODEX, "episode", "12", "completed", run_id="run-1", unit="ep04")
    queue.release(conn, CODEX, "episode", "ep04", "run-1")
    row = _row(conn, "ep04")
    assert (row["state"], row["claimed_by"], row["lease_until"], row["run_id"]) == ("done", None, None, "run-1")
    queue.release(conn, CODEX, "episode", "ep09", "run-1")  # no row: a no-op


def test_release_returns_an_untouched_claim_to_the_queue_for_the_desk_to_settle(conn, cpu_stage):
    """Every step skipped: no event of the run moved the row (C2's map leaves a
    `skipped` alone), so the claim is undone and the tick settles it done from
    the disk -- never a running row with a lease that expires into `stale`."""
    _order(conn, "ep04", "queued")
    queue.claim(conn, CODEX, "episode", "ep04", "run-1")
    db.add_event(conn, CODEX, "episode", "01", "skipped", run_id="run-1", unit="ep04")
    queue.release(conn, CODEX, "episode", "ep04", "run-1")
    row = _row(conn, "ep04")
    assert (row["state"], row["claimed_by"], row["lease_until"]) == ("queued", None, None)


def test_release_keeps_the_lease_of_a_run_that_died_without_a_terminal_event(conn, cpu_stage):
    """A started with no completed/failed after it: the row stays running and
    leased, so the desk's sweep marks it stale when the lease runs out."""
    _order(conn, "ep04", "queued")
    queue.claim(conn, CODEX, "episode", "ep04", "run-1")
    db.add_event(conn, CODEX, "episode", "03", "started", run_id="run-1", unit="ep04")
    queue.release(conn, CODEX, "episode", "ep04", "run-1")
    row = _row(conn, "ep04")
    assert row["state"] == "running" and row["claimed_by"] and row["lease_until"]


# --- the explicit form ---


def test_explicit_claim_words(conn, cpu_stage):
    assert queue.explicit_claim(conn, CODEX, "episode", "ep01", "run-1") == ("none", "")
    _order(conn, "ep02", "queued")
    assert queue.explicit_claim(conn, CODEX, "episode", "ep02", "run-1") == ("claimed", "")
    assert (_row(conn, "ep02")["state"], _row(conn, "ep02")["run_id"]) == ("running", "run-1")
    _order(conn, "ep03", "blocked", blocked_on="refs/04")
    assert queue.explicit_claim(conn, CODEX, "episode", "ep03", "run-1") == ("blocked", "refs/04")
    _order(conn, "ep04", "deferred")
    assert queue.explicit_claim(conn, CODEX, "episode", "ep04", "run-1") == ("deferred", "")
    assert _row(conn, "ep04")["claimed_by"] is None


def test_explicit_claim_names_the_hold_on_a_held_row(conn, cpu_stage):
    _order(conn, "ep05", "queued")
    hold_id = work_orders.hold(conn, "unit", "ep05 waits for the recast", codex_id=CODEX,
                               stage="episode", unit="ep05")
    tick.park_held(conn, CODEX, "episode", "ep05")
    word, why = queue.explicit_claim(conn, CODEX, "episode", "ep05", "run-1")
    assert word == "held"
    assert f"hold {hold_id}" in why and "recast" in why
    assert _row(conn, "ep05")["state"] == "held"


def test_explicit_claim_on_a_queued_row_the_gpu_index_refuses_is_contended(conn, monkeypatch):
    monkeypatch.setattr(queue, "stage_uses_gpu", lambda stage: True)
    db.claim_gpu(conn, _order(conn, "ep04", "queued"))
    _order(conn, "ep05", "queued")
    word, why = queue.explicit_claim(conn, CODEX, "episode", "ep05", "run-2")
    assert word == "contended" and "GPU" in why
    assert isinstance(conn.execute("SELECT COUNT(*) FROM work_orders").fetchone()[0], int)


def test_queue_never_sleeps_or_polls():
    """The no-unit form takes what is queued now and exits (decision, "Not
    built, on purpose"): the module knows no sleep, no poll, no loop."""
    import ast
    import inspect
    tree = ast.parse(inspect.getsource(queue))
    nodes = list(ast.walk(tree))
    assert not any(isinstance(n, ast.While) for n in nodes)
    calls = [n.func.attr if isinstance(n.func, ast.Attribute) else getattr(n.func, "id", "")
             for n in nodes if isinstance(n, ast.Call)]
    assert "sleep" not in calls
    imported = [a.name for n in nodes if isinstance(n, ast.Import) for a in n.names]
    assert "time" not in imported
