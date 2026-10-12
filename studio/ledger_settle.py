"""What the events ledger says of a book-level unit (board review 2026-10-12;
decision architecture/decisions/2026-10-12_the_ledger_settles_book_stages.md).

The board only knew what a runner wrote into work_orders, so screenplays and
trailers that ran -- or failed -- read `queued, step – of N`.  The ledger is the
truth whenever it has a terminal event for the unit:

    done     the stage's last step completed (flags 1 when a later re-run failed)
    failed   no delivery, and the newest terminal event failed
    cursor   no delivery, no failure last: the step after the newest completed

Pure reads; studio.tick writes what this returns."""
from __future__ import annotations

import sqlite3

from studio import registry

TERMINAL = ("completed", "failed")
NOTE_CHARS = 160


def step_events(conn: sqlite3.Connection, codex_id: str, stage: str, unit: str) -> list[dict]:
    """The unit's top-level terminal step events, oldest first (substeps and skips left
    out); a book-level runner's NULL unit is the `book` unit."""
    ids = {e["id"] for e in registry.steps(stage)}
    rows = conn.execute("SELECT id, event_ts, step_id, event, detail FROM events WHERE codex_id = ? AND stage = ?"
                        " AND COALESCE(unit, 'book') = ? AND event IN ('completed', 'failed') ORDER BY id",
                        (codex_id, stage, unit))
    return [dict(r) for r in rows if r["step_id"] in ids]


def next_step(stage: str, step_id: str) -> str:
    """The registry step after `step_id`; the last step stays itself."""
    ids = [e["id"] for e in registry.steps(stage)]
    k = ids.index(step_id) if step_id in ids else len(ids) - 1
    return ids[min(k + 1, len(ids) - 1)]


def said(event: dict) -> str:
    """`03 on 2026-09-07: 1 validation error …` -- an event in one clipped line."""
    detail = " ".join(str(event.get("detail") or "").split())[:NOTE_CHARS]
    return f"{event['step_id']} on {str(event['event_ts'])[:10]}" + (f": {detail}" if detail else "")


def delivered(events: list[dict], last_step: str, stage: str) -> dict:
    """The reading of a unit whose last step completed: done, flagged by a later failure."""
    last = [e for e in events if e["step_id"] == last_step and e["event"] == "completed"][-1]
    later = [e for e in events if e["event"] == "failed" and e["id"] > last["id"]]
    note = f"a re-run failed at {said(later[-1])}" if later else f"settled from the ledger: {last_step} completed"
    return {"state": "done", "step_id": last_step, "flags": int(bool(later)), "note": note,
            "finished_at": last["event_ts"]}


def reading(events: list[dict], last_step: str, stage: str) -> dict | None:
    """{state, step_id, flags, note, finished_at} the ledger says (state None = a cursor
    only); None when the unit has no terminal event."""
    if not events:
        return None
    if any(e["step_id"] == last_step and e["event"] == "completed" for e in events):
        return delivered(events, last_step, stage)
    newest = events[-1]
    if newest["event"] == "failed":
        return {"state": "failed", "step_id": newest["step_id"], "flags": 0,
                "note": f"failed at {said(newest)}", "finished_at": None}
    return {"state": None, "step_id": next_step(stage, newest["step_id"]), "flags": 0, "note": None,
            "finished_at": None}
