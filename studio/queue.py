"""The pull: how a runner takes its department's rows (decision 2026-09-25,
"How a department is driven", "The GPU", "Explicit invocation").

    queued_units    one book's department, the units the desk has queued, in
                    v_queue order (priority, sequence, unit)
    queued_books    the books whose (department, unit) row is queued -- a
                    book-level runner's ready() list
    claim           queued -> running under this run: claimed_by, lease_until
                    (15 min), run_id, the stage's GPU flag.  False when the row
                    is not queued any more (another run took it, the desk moved
                    it, it never existed) or the GPU index refuses a second
                    running GPU row (an IntegrityError, swallowed)
    renew           the lease pushed forward by the writes the runner already
                    makes (Tracker.event); a row not running is left alone
    release         the claim undone when the run ends: claimed_by and
                    lease_until cleared; a row the run never moved (every
                    step skipped) goes back to `queued` for the desk to settle
    explicit_claim  the `<book> <n>` form's word on its own row

No loop, no sleep, no poll: the no-unit form takes what is queued NOW and
exits ("Not built, on purpose" -- a queued row is a request until the owner
says it is an instruction).  Nothing here decides whether a step is done:
the disk does.  The runners call these by name; the grep test keeps the row's
writer inside db.
"""
from __future__ import annotations

import os
import platform
import sqlite3
from datetime import timedelta

from studio import db

LEASE_SECONDS = 900
"""The GPU lease (decision: 15 min), renewed by every event the run writes."""
_KEY = "codex_id = ? AND stage = ? AND unit = ?"


def _now() -> str:
    return db.utc_now().strftime("%Y-%m-%dT%H:%M:%SZ")


def lease_until(seconds: int = LEASE_SECONDS) -> str:
    """The lease's end, UTC, in the tick's format (its sweep compares strings)."""
    return (db.utc_now() + timedelta(seconds=seconds)).strftime("%Y-%m-%dT%H:%M:%SZ")


def claimant() -> str:
    """Who holds the claim: host:pid -- the process a stale lease points at."""
    return f"{platform.node()}:{os.getpid()}"


def stage_uses_gpu(stage: str) -> bool:
    """Whether any of the stage's steps puts a job on ComfyUI (the modules'
    GPU flag; the registry carries none).  A lazy import: the step modules are
    the runner's to load."""
    from studio import step_runner
    return any(getattr(step, "GPU", False) for step in step_runner.load_steps(stage))


# --- reading the queue ---


def queued_units(conn: sqlite3.Connection, codex_id: str, stage: str) -> list[str]:
    """The units of one book's department the desk has queued, first to run first."""
    return [row["unit"] for row in conn.execute(
        "SELECT unit FROM v_queue WHERE codex_id = ? AND stage = ?"
        " ORDER BY priority, sequence, unit", (codex_id, stage))]


def queued_books(conn: sqlite3.Connection, stage: str, unit: str) -> list[str]:
    """The books whose (department, unit) row is queued, first to run first."""
    return [row["codex_id"] for row in conn.execute(
        "SELECT codex_id FROM v_queue WHERE stage = ? AND unit = ?"
        " ORDER BY priority, sequence, codex_id", (stage, unit))]


def has_rows(conn: sqlite3.Connection, stage: str) -> bool:
    """Whether the desk has ever materialized a row for the department: a
    database no tick reached falls back to the events rule in the runners."""
    return conn.execute("SELECT 1 FROM work_orders WHERE stage = ? LIMIT 1", (stage,)).fetchone() is not None


# --- the claim ---


def claim(conn: sqlite3.Connection, codex_id: str, stage: str, unit: str, run_id: str,
          lease_seconds: int = LEASE_SECONDS) -> bool:
    """queued -> running under this run; True when the row was taken.  False
    when it is not queued (any more), or when the partial unique index refuses
    a second running GPU row -- one GPU, one claim."""
    try:
        cur = conn.execute(
            f"UPDATE work_orders SET state = 'running', claimed_by = ?, lease_until = ?, run_id = ?,"
            f" gpu = ?, updated_at = ? WHERE {_KEY} AND state = 'queued'",
            (claimant(), lease_until(lease_seconds), run_id, int(stage_uses_gpu(stage)), _now(),
             codex_id, stage, unit))
    except sqlite3.IntegrityError:
        conn.rollback()
        return False
    conn.commit()
    return cur.rowcount == 1


def renew(conn: sqlite3.Connection, codex_id: str, stage: str, unit: str,
          lease_seconds: int = LEASE_SECONDS) -> bool:
    """A running row's lease pushed forward; True when a row was renewed.  A
    row in any other state, or none, is a no-op: the lease belongs to a run."""
    cur = conn.execute(
        f"UPDATE work_orders SET lease_until = ?, updated_at = ? WHERE {_KEY} AND state = 'running'",
        (lease_until(lease_seconds), _now(), codex_id, stage, unit))
    conn.commit()
    return cur.rowcount == 1


def _run_moved_the_row(conn: sqlite3.Connection, codex_id: str, stage: str, unit: str,
                       run_id: str) -> bool:
    """Whether any event of this run but a `skipped` reached the unit -- a
    `started` is what moves a row (C2's map leaves a skipped alone)."""
    return conn.execute(
        "SELECT 1 FROM events WHERE run_id = ? AND codex_id = ? AND stage = ? AND unit = ?"
        " AND event != 'skipped' LIMIT 1", (run_id, codex_id, stage, unit)).fetchone() is not None


def release(conn: sqlite3.Connection, codex_id: str, stage: str, unit: str, run_id: str) -> None:
    """The claim undone when the run ends.  The state is add_event's (the last
    event's word); only the claim columns are cleared -- except that a row still
    `running` keeps its lease when the run wrote a `started` (it died without
    a terminal event; the sweep marks it stale), and goes back to `queued`
    when it wrote none (every step skipped; the desk settles it from the disk)."""
    row = db.work_order(conn, codex_id, stage, unit)
    if row is None:
        return
    if row["state"] == "running":
        if _run_moved_the_row(conn, codex_id, stage, unit, run_id):
            return
        conn.execute(f"UPDATE work_orders SET state = 'queued' WHERE {_KEY}", (codex_id, stage, unit))
    conn.execute(f"UPDATE work_orders SET claimed_by = NULL, lease_until = NULL, updated_at = ?"
                 f" WHERE {_KEY}", (_now(), codex_id, stage, unit))
    conn.commit()


# --- the explicit form ---


def explicit_claim(conn: sqlite3.Connection, codex_id: str, stage: str, unit: str,
                   run_id: str) -> tuple[str, str]:
    """The `<book> <n>` form's word on its own row, as (word, why):

      none       no row -- a book the desk never ticked: the runner runs as before
      claimed    the row was queued and is now this run's
      held       a hold reaches the row: the runner REFUSES; why names the hold
      contended  queued, but the GPU index refused (another GPU row is running);
                 the runner WARNS and runs -- ComfyUI's own queue is the real guard
      blocked    the desk names an upstream want (why = blocked_on): the runner
                 WARNS and runs -- the disk, not the row, is the truth of a step
      <state>    done, failed, deferred, escalated, stale, running: the same WARN;
                 the explicit form is the owner's hand and it runs
    """
    row = db.work_order(conn, codex_id, stage, unit)
    if row is None:
        return "none", ""
    if row["state"] == "held":
        return "held", ": ".join(s for s in (row["blocked_on"], row["hold_reason"]) if s)
    if row["state"] == "queued":
        if claim(conn, codex_id, stage, unit, run_id):
            return "claimed", ""
        return "contended", "the GPU row is running under another unit"
    return row["state"], row["blocked_on"] or ""
