"""The pulse (panel ruling 2026-10-04, contract C1): `GET /api/pulse.json`.

One small JSON, polled every two seconds by every open page, says for each
section of the board a fingerprint -- a short digest of cheap DB aggregates
(the newest work-order write, the newest order and its taking, the holds) and
an age bucket for sections that print ages -- so a page refetches a section
only when the studio changed it.  Two changes never write a row and must still
move the fingerprints: a running lease passing NOW (views.LAPSED_SQL shows the
row as stale -- a pure clock flip, counted into every fingerprint whose section
shows it) and a write landing within the same second as the last (stamps are
to the second, so each scope's fingerprint carries a concat of its rows).
It also carries what the shell draws (the "needs you" count, the queue, the
department dots, the pins, the GPU card, the studio hold) and the events
after the client's cursor.  Reads only; the GPU
card's progress (files + the process list) is read at most once per TTL."""
from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Callable
from datetime import datetime, timezone

from studio import eta, registry
from studio.command_center import views

RECENT_S = 24 * 3600
"""A unit or book written within this window (or running, or held) has its own key."""
EVENTS_CAP = 20
GPU_TTL_S = 4.0
ATTENTION_SQL = ("state IN ('failed', 'deferred', 'escalated', 'stale')"
                 f" OR {views.LAPSED_SQL}"
                 " OR (state = 'done' AND flags > 0)")
ROWS_CONCAT = ("GROUP_CONCAT(id || state || COALESCE(step_id, '') || COALESCE(progress, '')"
               " || COALESCE(flags, 0) || COALESCE(updated_at, '') ORDER BY id)")
"""What a scope's rows show, as one string: a write within the same second as
the last (stamps are to the second) still moves the scope's fingerprint."""


# --- the pure parts ---


def digest(*parts) -> str:
    """Eight hex characters standing for the parts."""
    return hashlib.blake2b(repr(parts).encode(), digest_size=4).hexdigest()


def bucket(now: float, newest: float | None, running: bool = False) -> str:
    """The age bucket a section's ages need: by the minute while its youngest row is
    under an hour old (or something runs), by the hour under a day, else by the day."""
    age = now - newest if newest is not None else float("inf")
    if running or age < 3600:
        return f"m{int(now // 60)}"
    return f"h{int(now // 3600)}" if age < 86400 else f"d{int(now // 86400)}"


def epoch(ts: str | None) -> float | None:
    """An ISO stamp as epoch seconds; None for none."""
    return eta.to_epoch(ts) if ts else None


def iso(now: float) -> str:
    """Epoch seconds as the DB writes its stamps (`2026-10-04T19:21:00Z`)."""
    return datetime.fromtimestamp(now, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def frac(p: dict) -> float | None:
    """How far the run is from its start to its finish, clamped to 0..1."""
    finish, start = (p.get("eta") or {}).get("finish_at"), p.get("run_started")
    if not finish or not start or finish <= start:
        return None
    return round(min(1.0, max(0.0, (p["now"] - start) / (finish - start))), 3)


class Ttl:
    """A value per key, read again only after `ttl` seconds."""

    def __init__(self, ttl: float):
        self.ttl, self.items = ttl, {}

    def get(self, key, now: float, read: Callable[[], object]):
        hit = self.items.get(key)
        if hit is None or now - hit[0] >= self.ttl:
            hit = (now, read())
            self.items[key] = hit
        return hit[1]


# --- the aggregates ---


def totals(conn: sqlite3.Connection) -> dict:
    """The studio-wide marks: work orders (with their row concat), orders, holds,
    the lapsed-lease count (the clock flip), the newest event."""
    one = lambda sql: tuple(conn.execute(sql).fetchone())
    return {"wo": one("SELECT COUNT(*), MAX(updated_at), COALESCE(SUM(state = 'running'), 0),"
                      f" {ROWS_CONCAT} FROM work_orders"),
            "lapsed": one(f"SELECT COUNT(*) FROM work_orders WHERE {views.LAPSED_SQL}"),
            "orders": one("SELECT MAX(id), MAX(taken_ts), MAX(ts) FROM orders"),
            "holds": one("SELECT MAX(id), COUNT(lifted_at), MAX(lifted_at) FROM holds"),
            "attention": one("SELECT COUNT(*), MAX(updated_at), GROUP_CONCAT(id || state || COALESCE(step_id, '') || flags)"
                             f" FROM work_orders WHERE {ATTENTION_SQL}"),
            "event": one("SELECT MAX(id) FROM events")[0] or 0}


def section_fps(t: dict, now: float) -> dict[str, str]:
    """The studio-wide sections' fingerprints; floor and lanes show the stale
    flip, so they carry the lapsed count too."""
    running, newest = bool(t["wo"][2]), epoch(t["wo"][1])
    return {"floor": digest(t["wo"], t["event"], t["holds"], t["lapsed"], bucket(now, newest, running)),
            "attention": digest(t["attention"], t["orders"], bucket(now, epoch(t["attention"][1]))),
            "orders": digest(t["orders"], bucket(now, epoch(t["orders"][2]))),
            "lanes": digest(t["wo"], t["event"], t["lapsed"], bucket(now, newest, running))}


def group_marks(conn: sqlite3.Connection, column: str, where: str = "1", args: tuple = ()) -> dict:
    """{value of column: (count, newest write, running, lapsed, row concat)} over the work orders."""
    rows = conn.execute(f"SELECT {column}, COUNT(*), MAX(updated_at), COALESCE(SUM(state = 'running'), 0),"
                        f" COALESCE(SUM({views.LAPSED_SQL}), 0), {ROWS_CONCAT}"
                        f" FROM work_orders WHERE {where} GROUP BY {column}", args)
    return {r[0]: tuple(r[1:]) for r in rows}


def event_marks(conn: sqlite3.Connection) -> tuple[dict[str, int], dict[str, int]]:
    """({stage: newest event id}, {codex: newest event id}) in one covering-index scan."""
    stages: dict[str, int] = {}
    books: dict[str, int] = {}
    for codex, stage, newest in conn.execute("SELECT codex_id, stage, MAX(id) FROM events GROUP BY codex_id, stage"):
        stages[stage] = max(stages.get(stage, 0), newest)
        books[codex] = max(books.get(codex, 0), newest)
    return stages, books


def mark_fp(mark: tuple | None, event: int | None, holds: tuple, now: float) -> str:
    """A department's or a book's fingerprint from its group mark and newest event."""
    mark = mark or (0, None, 0, 0, None)
    return digest(mark, event, holds, bucket(now, epoch(mark[1]), bool(mark[2])))


def unit_row(conn: sqlite3.Connection, stage: str, codex: str, unit: str) -> tuple | None:
    """The columns a unit's sections show -- last whether its lease lapsed
    (the clock flip) -- or None for no row."""
    row = conn.execute("SELECT state, step_id, progress, flags, updated_at, verdicts, (SELECT MAX(e.id) FROM events e"
                       " WHERE e.codex_id = w.codex_id AND e.stage = w.stage AND COALESCE(e.unit, 'book') = w.unit),"
                       f" {views.LAPSED_SQL}"
                       " FROM work_orders w WHERE stage = ? AND codex_id = ? AND unit = ?", (stage, codex, unit)).fetchone()
    return tuple(row) if row else None


def unit_orders(conn: sqlite3.Connection, stage: str, codex: str, unit: str) -> tuple:
    """The newest order on one unit and its taking."""
    return tuple(conn.execute("SELECT MAX(id), MAX(taken_ts) FROM orders WHERE scope = 'unit' AND stage = ?"
                              " AND codex_id = ? AND unit = ?", (stage, codex, unit)).fetchone())


def unit_fp(row: tuple | None, orders: tuple, holds: tuple, now: float) -> str:
    """A unit's fingerprint: its row, its orders, the holds, its age bucket."""
    newest, running = (epoch(row[4]), row[0] == "running") if row else (None, False)
    return digest(row, orders, holds, bucket(now, newest, running))


# --- the fingerprints ---


def recent_units(conn: sqlite3.Connection, now: float) -> list[tuple[str, str, str]]:
    """(stage, codex, unit) of every unit running, held or written within RECENT_S."""
    return [tuple(r) for r in conn.execute(
        "SELECT stage, codex_id, unit FROM work_orders WHERE state IN ('running', 'held') OR updated_at >= ?"
        " ORDER BY stage, codex_id, unit", (iso(now - RECENT_S),))]


def scoped_fps(conn: sqlite3.Connection, t: dict, now: float) -> dict[str, str]:
    """`dept:<stage>` for every registered stage, `book:<codex>` for the recent books."""
    stages = group_marks(conn, "stage")
    books = group_marks(conn, "codex_id", "codex_id IN (SELECT codex_id FROM work_orders WHERE"
                        " state IN ('running', 'held') OR updated_at >= ?)", (iso(now - RECENT_S),))
    by_stage, by_book = event_marks(conn)
    out = {f"dept:{s}": mark_fp(stages.get(s), by_stage.get(s), t["holds"], now) for s in registry.stage_names()}
    out.update({f"book:{c}": mark_fp(m, by_book.get(c), t["holds"], now) for c, m in books.items()})
    return out


def fingerprints(conn: sqlite3.Connection, now: float) -> dict[str, str]:
    """Every fingerprint but the shell's: the sections, the departments, the
    recent books and the recent units."""
    t = totals(conn)
    out = {**section_fps(t, now), **scoped_fps(conn, t, now)}
    for stage, codex, unit in recent_units(conn, now):
        out[f"unit:{stage}/{codex}/{unit}"] = unit_fp(unit_row(conn, stage, codex, unit),
                                                      unit_orders(conn, stage, codex, unit), t["holds"], now)
    return out


def fingerprint(conn: sqlite3.Connection, key: str, now: float) -> str:
    """One key's fingerprint, the same as `fingerprints` gives it -- also for a
    unit, a department or a book the map leaves out as not recent."""
    t = totals(conn)
    kind, _, rest = key.partition(":")
    if kind == "unit" and rest.count("/") == 2:
        stage, codex, unit = rest.split("/")
        return unit_fp(unit_row(conn, stage, codex, unit), unit_orders(conn, stage, codex, unit), t["holds"], now)
    if kind in ("dept", "book"):
        marks = group_marks(conn, "stage" if kind == "dept" else "codex_id")
        events = event_marks(conn)[0 if kind == "dept" else 1]
        return mark_fp(marks.get(rest), events.get(rest), t["holds"], now)
    return section_fps(t, now).get(key, "")


# --- the shell ---


def dept_dots(conn: sqlite3.Connection) -> dict[str, dict[str, int]]:
    """{stage: {shown state: n}} for every registered stage, zero counts left out."""
    out: dict[str, dict[str, int]] = {s: {} for s in registry.stage_names()}
    for stage, shown, n in conn.execute(
            f"SELECT stage, {views.SHOWN_SQL}, COUNT(*) FROM work_orders GROUP BY 1, 2 ORDER BY 1, 2"):
        if stage in out:
            out[stage][shown] = n
    for row in views.lapsed_rows(conn):                   # a carried lapse counts as running
        if row["stage"] in out and views.carried(row):
            d = out[row["stage"]]
            d["stale"] = d.get("stale", 1) - 1
            if d["stale"] < 1:
                d.pop("stale", None)
            d["running"] = d.get("running", 0) + 1
    return out


def running_rows(conn: sqlite3.Connection) -> list[dict]:
    """The running work orders, the GPU's first, as the views show them; a
    lapsed lease stays running while a process carries it (views.carried)."""
    return [v for v in (views.row_view(r) for r in conn.execute(
        "SELECT * FROM work_orders WHERE state = 'running' ORDER BY gpu DESC, started_at, id"))
        if v["shown"] == "running"]


def pin(row: dict) -> dict:
    """A running unit as the sidebar pins it."""
    step = " ".join(x for x in (row.get("step_id"), row.get("step_name"), row.get("progress")) if x)
    return {"href": f"/d/{row['stage']}/{row['codex_id']}/{row['unit']}",
            "label": f"{row['unit']} · {step}" if step else row["unit"], "state": row["shown"]}


def studio_hold(conn: sqlite3.Connection) -> dict | None:
    """The oldest open studio-wide hold as {id, since, reason}, else None."""
    row = conn.execute("SELECT id, held_at, reason FROM holds WHERE lifted_at IS NULL AND scope = 'studio'"
                       " ORDER BY id LIMIT 1").fetchone()
    return {"id": row[0], "since": row[1], "reason": row[2]} if row else None


def gpu(rows: list[dict], hold: dict | None, progress: Callable[[str, str], dict | None]) -> dict | None:
    """The GPU card: the unit holding the GPU (else the first running) with its
    step and, for an episode, its finish and liveness; held-only when a studio
    hold stands with nothing running; None when idle."""
    if not rows:
        return {"href": None, "unit": None, "step": None, "frac": None, "finish": None,
                "vital": None, "held": True} if hold else None
    row = rows[0]
    p = (progress(row["codex_id"], row["unit"]) if row["stage"] == "episode" else None) or {}
    return {"href": pin(row)["href"], "unit": row["unit"], "step": " ".join(
        x for x in (row.get("step_id"), row.get("step_name")) if x), "frac": frac(p) if p else None,
            "finish": (p.get("eta") or {}).get("finish") or None, "vital": p.get("vital"), "held": bool(hold)}


def shell_block(conn: sqlite3.Connection, progress: Callable[[str, str], dict | None]) -> dict:
    """What the shell draws, as numbers: needs you, the queue, the dots, the pins,
    the GPU card and the studio hold."""
    rows, hold = running_rows(conn), studio_hold(conn)
    return {"needs": views.inbox_count(conn), "queue": int(conn.execute("SELECT COUNT(*) FROM v_queue").fetchone()[0]),
            "dept_dots": dept_dots(conn), "pins": [pin(r) for r in rows], "gpu": gpu(rows, hold, progress),
            "hold": hold}


def shell_fp(block: dict) -> str:
    """The shell's fingerprint: everything it draws but the bar's fill, which moves every pulse."""
    still = {**block, "gpu": {**block["gpu"], "frac": None} if block["gpu"] else None}
    return digest(json.dumps(still, sort_keys=True))


# --- the events ---


def event_text(row: sqlite3.Row) -> str:
    """`ep17 · 08 panels completed`."""
    name = views.step_names(row["stage"]).get(row["step_id"], "")
    step = f"{row['step_id']} {name}".strip()
    return f"{row['unit'] or 'book'} · {step} {row['event']}"


def events_since(conn: sqlite3.Connection, since: int, cap: int = EVENTS_CAP) -> list[dict]:
    """The events after the cursor, newest first, at most `cap`."""
    rows = conn.execute("SELECT id, event_ts, codex_id, stage, step_id, event, unit FROM events WHERE id > ?"
                        " ORDER BY id DESC LIMIT ?", (since, cap))
    return [{"id": r["id"], "ts": r["event_ts"], "href": f"/d/{r['stage']}/{r['codex_id']}/{r['unit'] or 'book'}",
             "unit": r["unit"] or "book", "text": event_text(r)} for r in rows]


def orders_taken_since(conn: sqlite3.Connection, since: int, cap: int = EVENTS_CAP) -> list[dict]:
    """The orders a run took after the cursor's event, newest first (their receipts)."""
    row = conn.execute("SELECT event_ts FROM events WHERE id = ?", (since,)).fetchone()
    after = row[0][:19] + "Z" if row else ""
    rows = conn.execute("SELECT * FROM orders WHERE taken_ts IS NOT NULL AND taken_ts > ?"
                        " ORDER BY taken_ts DESC, id DESC LIMIT ?", (after, cap))
    return [{"id": f"ord-{r['id']}", "order": r["id"], "ts": r["taken_ts"], "unit": r["unit"] or r["scope"],
             "href": f"/d/{r['stage']}/{r['codex_id']}/{r['unit']}" if r["scope"] == "unit" else None,
             "text": f"{r['kind']} on {views.order_target(r)} taken by run {r['taken_by_run']}"} for r in rows]


def feed(conn: sqlite3.Connection, since: int | None) -> list[dict]:
    """The events and order receipts after the cursor, newest first, capped; none without a cursor."""
    if since is None:
        return []
    items = events_since(conn, since) + orders_taken_since(conn, since)
    return sorted(items, key=lambda e: e["ts"], reverse=True)[:EVENTS_CAP]


# --- the whole ---


def pulse(conn: sqlite3.Connection, now: float, boot: float, since: int | None,
          progress: Callable[[str, str], dict | None]) -> dict:
    """The C1 body."""
    block = shell_block(conn, progress)
    return {"boot": boot, "now": now, "fp": {"shell": shell_fp(block), **fingerprints(conn, now)},
            "shell": block, "events": feed(conn, since), "cursor": totals(conn)["event"]}
