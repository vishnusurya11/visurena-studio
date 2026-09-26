"""The hand: holds and orders over the department tables (decision
2026-09-25, "Owner actions" and "The GPU").

    holds    a brake at studio, book or unit scope; RENDER_HOLD mirrored in
    orders   the owner's intent, one writer: hold | lift | redo | bump | retry | requeue

A runner takes the orders addressed to its unit at the top of `run_steps`
(`take_orders`), and taking APPLIES them to the unit's work-order row: a bump
puts it first, a retry queues a deferred or failed row once, a requeue queues
any row but a running one, a redo lands on the row's `redo` list so the named
step runs although its output exists.  A hold and a lift are applied by
`hold()` and `lift()` themselves; the order row is their receipt.  A redo's
note is also one owner row in the casebook, through the door note.py uses.
Nothing here runs a step or reads the disk for a state.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from studio import casebook, db, episode_home

KINDS = ("hold", "lift", "redo", "bump", "retry", "requeue")
SCOPES = ("studio", "book", "unit")
RENDER_HOLD = "RENDER_HOLD"
"""The reason of the studio-scope hold that mirrors the file."""

_APPLIES_TO = ("scope = 'studio' OR (scope = 'book' AND codex_id = ?)"
               " OR (scope = 'unit' AND codex_id = ? AND stage = ? AND unit = ?)")
"""A studio row reaches everything, a book row its book, a unit row its unit."""


def _now() -> str:
    return db.utc_now().strftime("%Y-%m-%dT%H:%M:%SZ")


def _check_scope(scope: str, codex_id: str | None, stage: str | None, unit: str | None) -> None:
    """A scope names what it reaches: a book needs its codex_id, a unit its three ids."""
    if scope not in SCOPES:
        raise ValueError(f"scope {scope!r} is not one of {SCOPES}")
    if scope in ("book", "unit") and not codex_id:
        raise ValueError(f"a {scope}-scope row needs its codex_id")
    if scope == "unit" and not (stage and unit):
        raise ValueError("a unit-scope row needs its stage and unit")


def order(conn: sqlite3.Connection, kind: str, scope: str, *, codex_id: str | None = None,
          stage: str | None = None, unit: str | None = None, step_id: str | None = None,
          note: str | None = None, by: str = "owner", artefact: str | None = None,
          fault: str = "unknown") -> int:
    """One orders row, untaken; its id.  A redo with a note also notes the casebook
    (the note is about `artefact`, a book-relative path, of fault class `fault`)."""
    if kind not in KINDS:
        raise ValueError(f"kind {kind!r} is not one of {KINDS}")
    _check_scope(scope, codex_id, stage, unit)
    if kind == "redo" and note:
        _note_redo(codex_id, unit, artefact, fault, note)
    cur = conn.execute(
        "INSERT INTO orders (ts, kind, scope, codex_id, stage, unit, step_id, note, by)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (_now(), kind, scope, codex_id, stage, unit, step_id, note, by))
    conn.commit()
    return cur.lastrowid


def _note_redo(codex_id: str, unit: str, artefact: str | None, fault: str, note: str) -> Path:
    """The redo's words as an owner row in the book's casebook, before the order lands."""
    if not artefact:
        raise ValueError("a redo's note is about an artefact: name it (book-relative path)")
    return casebook.note_owner(episode_home.book_dir(codex_id), codex_id, unit, artefact, fault, note)


def hold(conn: sqlite3.Connection, scope: str, reason: str, *, codex_id: str | None = None,
         stage: str | None = None, unit: str | None = None, by: str = "owner") -> int:
    """A holds row (open) and its receipt in orders; the hold's id."""
    _check_scope(scope, codex_id, stage, unit)
    cur = conn.execute(
        "INSERT INTO holds (scope, codex_id, stage, unit, reason, held_by, held_at)"
        " VALUES (?, ?, ?, ?, ?, ?, ?)", (scope, codex_id, stage, unit, reason, by, _now()))
    hold_id = cur.lastrowid
    order(conn, "hold", scope, codex_id=codex_id, stage=stage, unit=unit, note=reason, by=by)
    return hold_id


def lift(conn: sqlite3.Connection, hold_id: int, by: str = "owner") -> int:
    """Close one hold (lifted_at) and receipt it in orders; the lift order's id."""
    row = conn.execute("SELECT * FROM holds WHERE id = ?", (hold_id,)).fetchone()
    if row is None:
        raise ValueError(f"no hold with id {hold_id}")
    if row["lifted_at"]:
        raise ValueError(f"hold {hold_id} was already lifted at {row['lifted_at']}")
    conn.execute("UPDATE holds SET lifted_at = ? WHERE id = ?", (_now(), hold_id))
    return order(conn, "lift", row["scope"], codex_id=row["codex_id"], stage=row["stage"],
                 unit=row["unit"], note=f"hold {hold_id}: {row['reason']}", by=by)


def active_holds(conn: sqlite3.Connection, codex_id: str | None = None, stage: str | None = None,
                 unit: str | None = None) -> list[sqlite3.Row]:
    """Every open hold that reaches the unit: studio holds always, book holds for
    its book, unit holds for it alone.  With no unit named, the studio holds."""
    return list(conn.execute(
        f"SELECT * FROM holds WHERE lifted_at IS NULL AND ({_APPLIES_TO}) ORDER BY id",
        (codex_id, codex_id, stage, unit)))


def is_held(conn: sqlite3.Connection, codex_id: str, stage: str, unit: str) -> bool:
    return bool(active_holds(conn, codex_id, stage, unit))


def _render_hold(conn: sqlite3.Connection) -> sqlite3.Row | None:
    """The open studio hold that mirrors the file, if there is one."""
    return conn.execute(
        "SELECT * FROM holds WHERE lifted_at IS NULL AND scope = 'studio' AND reason = ?"
        " ORDER BY id LIMIT 1", (RENDER_HOLD,)).fetchone()


def mirror_render_hold(conn: sqlite3.Connection, hold_path: Path) -> int | None:
    """The file into the table: a studio hold while RENDER_HOLD exists, lifted when
    it is gone.  The file STAYS the brake; this is the board's view of it.  The
    id of the mirrored hold, or None when the file is absent."""
    present, current = Path(hold_path).exists(), _render_hold(conn)
    if present and current is None:
        return hold(conn, "studio", RENDER_HOLD, by="file")
    if not present and current is not None:
        lift(conn, current["id"], by="file")
        return None
    return current["id"] if current else None


def pending_orders(conn: sqlite3.Connection, codex_id: str, stage: str, unit: str) -> list[sqlite3.Row]:
    """The untaken orders that reach the unit, oldest first."""
    return list(conn.execute(
        f"SELECT * FROM orders WHERE taken_ts IS NULL AND ({_APPLIES_TO}) ORDER BY id",
        (codex_id, codex_id, stage, unit)))


def take_orders(conn: sqlite3.Connection, codex_id: str, stage: str, unit: str,
                run_id: str) -> list[sqlite3.Row]:
    """Stamp every pending order with this run and apply it to the unit's row."""
    rows = pending_orders(conn, codex_id, stage, unit)
    for row in rows:
        apply = _APPLY.get(row["kind"])
        if apply:
            apply(conn, codex_id, stage, unit, row["step_id"])
        conn.execute("UPDATE orders SET taken_ts = ?, taken_by_run = ? WHERE id = ?",
                     (_now(), run_id, row["id"]))
    conn.commit()
    return rows


def _bump(conn, codex_id, stage, unit, step_id) -> None:
    """Priority 0: first in its department's queue."""
    db.upsert_work_order(conn, codex_id, stage, unit, priority=0)


def _retry(conn, codex_id, stage, unit, step_id) -> None:
    """A deferred or failed row goes back to the queue; any other row is left alone."""
    row = db.work_order(conn, codex_id, stage, unit)
    if row is not None and row["state"] in ("deferred", "failed"):
        db.upsert_work_order(conn, codex_id, stage, unit, state="queued")


def _requeue(conn, codex_id, stage, unit, step_id) -> None:
    """Back to the queue from any state but running (a row not yet made is made queued)."""
    row = db.work_order(conn, codex_id, stage, unit)
    if row is None or row["state"] != "running":
        db.upsert_work_order(conn, codex_id, stage, unit, state="queued")


def _redo(conn, codex_id, stage, unit, step_id) -> None:
    """The step joins the row's redo list (once)."""
    steps = redo_steps(conn, codex_id, stage, unit)
    if step_id and step_id not in steps:
        db.upsert_work_order(conn, codex_id, stage, unit, redo=json.dumps(sorted(steps | {step_id})))


_APPLY = {"bump": _bump, "retry": _retry, "requeue": _requeue, "redo": _redo}
"""hold and lift are applied by hold() and lift(); their order rows are receipts."""


def redo_steps(conn: sqlite3.Connection, codex_id: str, stage: str, unit: str) -> set[str]:
    """The steps the owner asked to run again although their output exists."""
    row = db.work_order(conn, codex_id, stage, unit)
    if row is None or not row["redo"]:
        return set()
    return set(json.loads(row["redo"]))


def clear_redo(conn: sqlite3.Connection, codex_id: str, stage: str, unit: str, step_id: str) -> None:
    """The step ran again: off the list (NULL when the list is empty)."""
    steps = redo_steps(conn, codex_id, stage, unit)
    if step_id not in steps:
        return
    rest = sorted(steps - {step_id})
    db.upsert_work_order(conn, codex_id, stage, unit, redo=json.dumps(rest) if rest else None)
