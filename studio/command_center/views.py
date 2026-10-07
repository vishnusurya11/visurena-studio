"""The view layer (report D §0): one row per (department, unit); every screen
is a projection of it.  Pure functions over (conn, library) returning the
dicts and lists the templates render and the JSON twins validate.  Reads only:
the rows the runners wrote, the files the steps wrote, the run's log.  The
vocabulary is D §2 -- a glyph and a colour per state, colour naming who the
row needs (red a developer, black the owner, amber nobody now, purple the
next pass, blue the GPU, green nobody).  No state is computed here that a
runner did not write; `flagged` is a done row with flags, as C3 ruled."""
from __future__ import annotations

import json
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

from studio import db, episode_home, eta, gate_policy, registry
from studio.command_center import library_paths, procs, thumbs

MARKS = {"queued": ("circle", "○"), "blocked": ("circle-dashed", "◌"), "running": ("loader", "●"),
         "done": ("check", "✓"), "flagged": ("flag", "⚑"), "deferred": ("corner-up-left", "↩"),
         "failed": ("x", "✕"), "escalated": ("hand", "✋"), "held": ("pause", "⏸"),
         "stale": ("history", "~"), "skipped": ("minus", "–")}
"""Each state's mark: its icon (a Lucide symbol in static/icons.svg, drawn with the
`icon()` macro) and its Unicode glyph -- the text fallback for titles, the tab's
name, the JSON twins and plain text."""
ICONS = {state: name for state, (name, _) in MARKS.items()}
GLYPHS = {state: mark for state, (_, mark) in MARKS.items()}
COLOURS = {"failed": "red", "stale": "red", "escalated": "black", "flagged": "amber",
           "deferred": "purple", "running": "blue", "done": "green"}
ATTENTION = ("escalated", "failed", "stale", "running", "deferred", "held", "flagged",
             "queued", "blocked", "done", "skipped")
LEGEND = [(GLYPHS[s], s) for s in ("queued", "blocked", "running", "done", "flagged", "deferred",
                                   "failed", "escalated", "held", "stale", "skipped")]
LOG_LEVELS = frozenset({"WARNING", "ERROR", "CRITICAL"})
TAIL_BYTES = 64 * 1024
THUMBS = {"episode": (("panels", "storyboard/shot_*.png"), ("takes", "reports/strip_*.png"),
                      ("master", "cut/master_iter*.mp4"))}
PASSED = frozenset({"approve", "approved", "pass", "passed", "ok", "accept", "accepted"})
FLAGGED_REASON = "shipped with flags, not acknowledged"
APPLIED = ("hold", "lift", "acknowledge")
"""Orders that act when given; a runner takes none of them."""


# --- the vocabulary ---


# A running row whose lease ran out is not running (decision 2026-09-25: an expired lease is
# `stale`). The tick writes that word only when it next runs; the board reads the rule itself.
# Every lease is written as YYYY-MM-DDTHH:MM:SSZ (studio/queue.py), so text order is time order.
LAPSED_SQL = ("(state = 'running' AND lease_until IS NOT NULL"
              " AND lease_until < strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))")
LIVE_SQL = f"(state = 'running' AND NOT {LAPSED_SQL})"
SHOWN_SQL = f"CASE WHEN {LAPSED_SQL} THEN 'stale' WHEN state = 'done' AND flags > 0 THEN 'flagged' ELSE state END"


def lease_lapsed(row: dict, now: datetime) -> bool:
    """A running row whose lease_until has passed: its run died without settling it."""
    until = row.get("lease_until")
    if row.get("state") != "running" or not until:
        return False
    try:
        return datetime.fromisoformat(str(until).replace("Z", "+00:00")) < now
    except ValueError:
        return False


def unit_tokens(unit: str) -> set[str]:
    """The command-line spellings of a unit's number (`ep04` -> 4, 04, ep04); empty when none."""
    digits = "".join(c for c in (unit or "") if c.isdigit())
    if not digits or not (unit or "").endswith(digits):
        return set()
    return {str(int(digits)), f"{int(digits):02d}", f"ep{int(digits):02d}"}


BOOK_CARRY_S = 6 * 3600
"""A book-wide carrier vouches only for a lease that starved within this window:
the autopilot names the book, never the unit, so a days-dead row (ep18) must not
revive just because the book is being worked."""
CARRIERS = ("drive.py", "autopilot.py", "episode.py")


FRESH_FILES_S = 45 * 60
"""How recently the unit's folder must have moved to vouch for a silent ledger:
longer than the longest render a healthy step goes quiet for."""


def _unit_carried(row: dict, rows: list) -> bool:
    """A process names this unit's number beside its codex."""
    wanted, codex = unit_tokens(row.get("unit") or ""), row.get("codex_id") or ""
    return bool(wanted) and bool(codex) and any(
        codex in p.cmdline and wanted & set(p.cmdline.replace('"', " ").split()) for p in rows)


def _files_carried(row: dict) -> bool:
    """The run's own files are still moving (ep23, 2026-10-07: the run's process
    was invisible to the API): the unit's folder or one of its child dirs has a
    fresh mtime -- a directory stamps when a file lands in it."""
    book = library_paths.book_folder(episode_home.LIBRARY, row.get("codex_id") or "")
    home = book / row["home"] if book and row.get("home") else None
    if home is None or not home.is_dir():
        return False
    now = utc_now().timestamp()
    stamps = [home.stat().st_mtime] + [d.stat().st_mtime for d in home.iterdir() if d.is_dir()]
    return any(now - s < FRESH_FILES_S for s in stamps)


def _book_carried(row: dict, rows: list) -> bool:
    """A carrier runs the whole book and this lease starved recently (ep23's
    autopilot, 2026-10-07)."""
    until = row.get("lease_until")
    try:
        age = (utc_now() - datetime.fromisoformat(str(until).replace("Z", "+00:00"))).total_seconds()
    except (TypeError, ValueError):
        return False
    codex = row.get("codex_id") or ""
    return age < BOOK_CARRY_S and bool(codex) and any(
        codex in p.cmdline and any(c in p.cmdline for c in CARRIERS) for p in rows)


def carried(row: dict, proc_rows: list | None = None) -> bool:
    """A lapsed running row is still alive while a process carries it: by its
    unit's number, or book-wide for a freshly starved lease (step 09 renders
    for long stretches without a ledger write, so the lease starves although
    the run is healthy)."""
    rows = procs.list_processes() if proc_rows is None else proc_rows
    return _unit_carried(row, rows) or _book_carried(row, rows) or _files_carried(row)


def lapsed_rows(conn: sqlite3.Connection) -> list[dict]:
    """The running rows whose lease has passed, raw."""
    return [dict(r) for r in conn.execute(f"SELECT * FROM work_orders WHERE {LAPSED_SQL}")]


def display_state(state: str, flags: int = 0) -> str:
    """What the row shows: `flagged` when a done unit carries judge flags."""
    return "flagged" if state == "done" and flags else state


def glyph(state: str, flags: int = 0) -> str:
    """D's glyph for a state; a flagged row shows its count (`⚑3`)."""
    shown = display_state(state, flags)
    mark = GLYPHS.get(shown, "?")
    return f"{mark}{flags}" if shown == "flagged" else mark


def colour_class(state: str) -> str:
    """Who the row needs, as a CSS class; grey when nobody and nothing runs."""
    return COLOURS.get(state, "grey")


def rank(row: dict) -> tuple:
    """Attention order: escalated, failed, stale, running, deferred, held,
    flagged, queued, blocked, done; then slate order, then the unit's name."""
    shown = row.get("shown") or display_state(row["state"], row.get("flags") or 0)
    return (ATTENTION.index(shown) if shown in ATTENTION else len(ATTENTION),
            row.get("sequence") if row.get("sequence") is not None else 10 ** 9, row["unit"])


# --- rows ---


@lru_cache(maxsize=16)
def step_names(stage: str) -> dict[str, str]:
    """{step_id: name} from the registry; {} for a stage it does not know."""
    try:
        return {e["id"]: e["name"] for e in registry.steps(stage)}
    except ValueError:
        return {}


def elapsed(started_at: str | None) -> str:
    """`1h42` / `7m` / `12s` since an ISO timestamp; '' without one."""
    if not started_at:
        return ""
    try:
        start = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
    except ValueError:
        return ""
    seconds = max(0, int((datetime.now(timezone.utc) - start).total_seconds()))
    if seconds >= 3600:
        return f"{seconds // 3600}h{(seconds % 3600) // 60:02d}"
    return f"{seconds // 60}m" if seconds >= 60 else f"{seconds}s"


def age(now: datetime, ts: str | None) -> str:
    """How old a stamp is, in one unit: `now`, `2 m`, `3 h`, `9 d`; '' without one."""
    try:
        then = datetime.fromisoformat(str(ts).replace("Z", "+00:00")) if ts else None
    except ValueError:
        then = None
    if then is None:
        return ""
    seconds = int((now - then).total_seconds())
    if seconds < 60:
        return "now"
    if seconds < 3600:
        return f"{seconds // 60} m"
    return f"{seconds // 3600} h" if seconds < 86400 else f"{seconds // 86400} d"


def utc_now() -> datetime:
    """The clock the ages are read against."""
    return datetime.now(timezone.utc)


def row_view(row: sqlite3.Row | dict) -> dict:
    """A work-order row as the templates read it: the columns, the verdicts
    JSON parsed, the shown state, its glyph and colour, the step's name, the
    age of its last write."""
    r = dict(row)
    r["verdicts"] = json.loads(r["verdicts"]) if r.get("verdicts") else {}
    lapsed = lease_lapsed(r, utc_now()) and not carried(r)
    state = "stale" if lapsed else r["state"]
    r["shown"] = display_state(state, r.get("flags") or 0)
    r["glyph"] = glyph(state, r.get("flags") or 0)
    r["css"] = colour_class(r["shown"])
    r["step_name"] = step_names(r["stage"]).get(r.get("step_id") or "", "")
    r["elapsed"] = elapsed(r.get("started_at")) if state == "running" else ""
    r["age"] = age(utc_now(), r.get("updated_at"))
    return r


def book_names(conn: sqlite3.Connection) -> dict[str, str]:
    """{codex_id: name} for the breadcrumbs."""
    return {r["id"]: r["name"] for r in conn.execute("SELECT id, name FROM codex")}


# --- the home and the floor ---


def floor(conn: sqlite3.Connection) -> dict:
    """On the floor: the running rows (the GPU's first) and the next four of
    the queue, in the order a runner would take them."""
    running = [v for v in (row_view(r) for r in conn.execute(
        "SELECT * FROM work_orders WHERE state = 'running' ORDER BY gpu DESC, started_at, id"))
        if v["shown"] == "running"]
    nxt = [row_view(r) for r in conn.execute("SELECT * FROM v_queue LIMIT 4")]
    return {"running": running, "next": nxt}


def queue(conn: sqlite3.Connection) -> list[dict]:
    """The whole queue, derived: priority, slate order, unit (v_queue)."""
    return [row_view(r) for r in conn.execute("SELECT * FROM v_queue")]


def attention(conn: sqlite3.Connection) -> list[dict]:
    """Needs you (research 07 §5): failed, deferred, escalated, stale -- oldest
    first, each with the detail its current step left -- then every unit that
    shipped with flags the owner has not acknowledged, oldest first.  Stale is
    derived, not just stored: a running row whose lease has lapsed is a dead
    run the tick has not named yet, and it needs a person now (referee D1)."""
    rows = conn.execute(
        "SELECT w.*, (SELECT s.detail FROM work_steps s WHERE s.order_id = w.id"
        " AND s.step_id = w.step_id) AS detail FROM work_orders w"
        f" WHERE w.state IN ('failed', 'deferred', 'escalated', 'stale') OR {LAPSED_SQL.replace('state', 'w.state').replace('lease_until', 'w.lease_until')}"
        " ORDER BY w.updated_at, w.id")
    needs = [v for v in (row_view(r) for r in rows) if v["shown"] != "running"]   # a carried lapse is alive
    return needs + flagged_unacknowledged(conn)


def inbox_count(conn: sqlite3.Connection) -> int:
    """How many rows Needs you holds -- the one number the sidebar, the badge,
    the pulse and the /inbox page all print."""
    return len(attention(conn))


def flagged_unacknowledged(conn: sqlite3.Connection) -> list[dict]:
    """The done rows with flags and no acknowledge for their current verdict
    state, each with its reason and its non-pass gates."""
    rows = conn.execute("SELECT * FROM work_orders WHERE state = 'done' AND flags > 0"
                        " ORDER BY updated_at, id").fetchall()
    return [{**row_view(r), "reason": FLAGGED_REASON,
             "gates": non_pass_gates(json.loads(r["verdicts"] or "{}"))}
            for r in rows if not db.acknowledged(conn, r["codex_id"], r["stage"], r["unit"])]


def non_pass_gates(verdicts: dict) -> list[str]:
    """`GATE ⚑n` / `GATE ✕` for every signed gate that did not pass clean."""
    out = []
    for gate, rec in verdicts.items():
        mark, css = verdict_glyph(rec or None)
        if css not in ("green", "grey"):
            out.append(f"{gate} {mark}")
    return out


def holds(conn: sqlite3.Connection) -> list[dict]:
    """Every open hold, oldest first, with its age."""
    now = utc_now()
    return [{**dict(r), "age": age(now, r["held_at"])}
            for r in conn.execute("SELECT * FROM holds WHERE lifted_at IS NULL ORDER BY id")]


def order_target(row: sqlite3.Row | dict) -> str:
    """Whom an order reaches: `studio`, the book's id, or `stage › unit` (with its step)."""
    r = dict(row)
    if r["scope"] == "studio":
        return "studio"
    if r["scope"] == "book":
        return r["codex_id"]
    step = f" · step {r['step_id']}" if r.get("step_id") else ""
    return f"{r['stage']} › {r['unit']}{step}"


def order_taken(row: sqlite3.Row | dict) -> str:
    """The run that took the order; a hold, lift or acknowledge not yet taken
    is already applied (it acts at once); any other untaken order is pending."""
    if row["taken_by_run"]:
        return row["taken_by_run"]
    return "applied" if row["kind"] in APPLIED else "pending"


def recent_orders(conn: sqlite3.Connection, limit: int = 10) -> list[dict]:
    """The last `limit` orders rows, newest first, each with its target, taker and age."""
    rows, now = conn.execute("SELECT * FROM orders ORDER BY id DESC LIMIT ?", (limit,)), utc_now()
    return [{**dict(r), "target": order_target(r), "taken": order_taken(r), "age": age(now, r["ts"])} for r in rows]


def lane(conn: sqlite3.Connection, stage: str) -> dict:
    """One department's lane: the count, counts by shown state, the glyph
    tally in attention order, and the six rows that matter most."""
    rows = sorted((row_view(r) for r in db.department_rows(conn, stage)), key=rank)
    counts = Counter(r["shown"] for r in rows)
    tally = [(GLYPHS[s], counts[s]) for s in ATTENTION if counts.get(s)]
    return {"stage": stage, "total": len(rows), "counts": dict(counts), "tally": tally,
            "bar": [r["css"] for r in rows], "rows": rows[:6]}


def shelf(conn: sqlite3.Connection) -> list[dict]:
    """Every book (codex row) by name, with how many units it has, how many
    run and how many are done -- the /books page."""
    rows = conn.execute(
        "SELECT c.id AS codex_id, c.name, COUNT(w.id) AS units,"
        f" COALESCE(SUM({LIVE_SQL.replace('state', 'w.state').replace('lease_until', 'w.lease_until')}), 0) AS running,"
        " COALESCE(SUM(w.state = 'done'), 0) AS done"
        " FROM codex c LEFT JOIN work_orders w ON w.codex_id = c.id GROUP BY c.id ORDER BY c.name, c.id")
    extra = Counter(r["codex_id"] for r in lapsed_rows(conn) if carried(r))
    return [dict(r) | {"running": r["running"] + extra.get(r["codex_id"], 0)} for r in rows]


def lanes(conn: sqlite3.Connection) -> list[dict]:
    """A lane per registered department, in stages.yaml order."""
    return [lane(conn, stage) for stage in registry.stage_names()]


def today(conn: sqlite3.Connection) -> list[dict]:
    """The steps that ended today (UTC), newest first, thirty at most."""
    rows = conn.execute(
        "SELECT s.step_id, s.state, s.attempt, s.ended_at, s.seconds, s.verdict_word, s.terminal,"
        " w.codex_id, w.stage, w.unit FROM work_steps s JOIN work_orders w ON w.id = s.order_id"
        " WHERE s.ended_at IS NOT NULL AND substr(s.ended_at, 1, 10) = strftime('%Y-%m-%d', 'now')"
        " ORDER BY s.ended_at DESC, s.step_id DESC LIMIT 30")
    out, now = [], utc_now()
    for r in rows:
        d = dict(r)
        d["step_name"] = step_names(d["stage"]).get(d["step_id"], "")
        d["glyph"], d["css"] = glyph(d["state"]), colour_class(d["state"])
        d["age"] = age(now, d["ended_at"])
        out.append(d)
    return out


# --- the queue's finish (P06.4: a clean pass is not a unit as run) ---


def clean_seconds(hist: dict[str, list[float]], from_step: str | None = None) -> float:
    """A clean pass: the p50 of every step at or after `from_step` (all without one)."""
    return sum(eta.band(xs)[1] for sid, xs in hist.items() if xs and (from_step is None or sid >= from_step))


def unit_walls(conn: sqlite3.Connection, stage: str) -> list[float]:
    """Seconds from first to last event of every done unit of the stage -- what a unit takes as run."""
    rows = conn.execute("SELECT MIN(e.event_ts), MAX(e.event_ts) FROM events e JOIN work_orders w ON w.id = e.order_id"
                        " WHERE w.stage = ? AND w.state = 'done' GROUP BY w.id", (stage,))
    walls = [(eta.to_epoch(b) or 0.0) - (eta.to_epoch(a) or 0.0) for a, b in rows]
    return [w for w in walls if w >= 0.0]


def lane_eta(now: float, clean_left: float, units: int, walls: list[float]) -> dict:
    """The lane's finish: `clean` at the p50s, `as_run` (with a p10-p90 band) at the
    units' measured first-to-last walls; no as-run without a done unit."""
    lo, mid, hi = eta.band(walls)
    run = (lambda w: now + units * w) if walls else (lambda w: None)
    return {"clean": now + clean_left, "as_run": run(mid), "as_run_lo": run(lo), "as_run_hi": run(hi),
            "units": units}


def day_span(lo: float, hi: float, tz) -> str:
    """`Tue–Thu`, or one day's name when both fall on it."""
    a, b = (datetime.fromtimestamp(x, tz).strftime("%a") for x in (lo, hi))
    same = datetime.fromtimestamp(lo, tz).date() == datetime.fromtimestamp(hi, tz).date()
    return a if same else f"{a}–{b}"


def eta_words(e: dict, tz) -> dict:
    """The KPI's words: `~Mon 05:29 if clean` and `as run Tue–Thu`."""
    clean = datetime.fromtimestamp(e["clean"], tz).strftime("~%a %H:%M if clean")
    as_run = f"as run {day_span(e['as_run_lo'], e['as_run_hi'], tz)}" if e["as_run"] else ""
    return {"clean_text": clean, "as_run_text": as_run}


_HISTORY: dict[tuple, dict] = {}


def stage_history(conn: sqlite3.Connection, stage: str) -> dict[str, list[float]]:
    """eta.step_history, read again only when a new event lands (per database file)."""
    key = (conn.execute("PRAGMA database_list").fetchone()[2], stage,
           conn.execute("SELECT MAX(id) FROM events").fetchone()[0])
    if key not in _HISTORY:
        _HISTORY.clear()
        _HISTORY[key] = eta.step_history(conn, stage)
    return _HISTORY[key]


def queue_eta(conn: sqlite3.Connection, stage: str = "episode", now: float | None = None, tz=None) -> dict | None:
    """When the stage's lane clears: the running units from their step, the queued
    ones whole, clean and as run, with the KPI's words; None when the lane is empty."""
    rows = conn.execute("SELECT state, step_id FROM work_orders WHERE stage = ? AND state IN ('running', 'queued')",
                        (stage,)).fetchall()
    if not rows:
        return None
    hist, now = stage_history(conn, stage), datetime.now(timezone.utc).timestamp() if now is None else now
    left = sum(clean_seconds(hist, r["step_id"] if r["state"] == "running" else None) for r in rows)
    e = lane_eta(now, left, len(rows), unit_walls(conn, stage))
    return {**e, **eta_words(e, tz)}


# --- verdicts ---


@lru_cache(maxsize=16)
def gate_order(stage: str) -> list[str]:
    """The department's gates in gates.yaml order; [] for a stage with none."""
    doc = gate_policy.load()
    return list((doc.get("gates") or {}).get(stage) or {})


def verdict_glyph(rec: dict | None) -> tuple[str, str]:
    """A gate's chip: unsigned ○; faults or `flagged` ⚑n amber; a deferring
    terminal ↩; a passing word ✓; anything else ✕ red."""
    if not rec:
        return "○", "grey"
    faults = int(rec.get("faults") or 0)
    word = str(rec.get("word") or "").lower()
    if faults or word == "flagged":
        return f"⚑{faults or ''}", "amber"
    if rec.get("terminal") == "defer":
        return "↩", "purple"
    return ("✓", "green") if word in PASSED else ("✕", "red")


def verdict_chip(gate: str, rec: dict | None) -> dict:
    """One chip of the strip, every key present."""
    rec = rec or {}
    mark, css = verdict_glyph(rec or None)
    return {"gate": gate, "word": str(rec.get("word") or ""), "glyph": mark, "css": css,
            "by": str(rec.get("by") or ""), "faults": int(rec.get("faults") or 0),
            "sha8": str(rec.get("sha8") or ""), "path": str(rec.get("path") or ""),
            "terminal": str(rec.get("terminal") or "")}


def verdict_strip(verdicts: dict, gates: list[str]) -> list[dict]:
    """The strip: gates.yaml's gates in order, then any the row carries that
    the file does not name."""
    order = list(gates) + [g for g in verdicts if g not in gates]
    return [verdict_chip(gate, verdicts.get(gate)) for gate in order]


# --- a department at a glance ---


def ago(ts: str | None) -> str:
    """`just now` / `12m ago` / `7h ago` / `3d ago` since an ISO timestamp."""
    if not ts:
        return ""
    try:
        then = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return ""
    minutes = max(0, int((datetime.now(timezone.utc) - then).total_seconds() // 60))
    if minutes < 1:
        return "just now"
    if minutes < 60:
        return f"{minutes}m ago"
    return f"{minutes // 60}h ago" if minutes < 24 * 60 else f"{minutes // (24 * 60)}d ago"


def gpu_hours(seconds: float | None) -> str:
    """GPU time as a person reads it: `9.8 h`, `23 m`, or a dash for none."""
    if not seconds:
        return "–"
    return f"{seconds / 3600:.1f} h" if seconds >= 3600 else f"{round(seconds / 60)} m"


STEP_CSS = {"skipped": "green"}
"""A skipped step's output was already on disk: it reads as done."""


def cursor_state(step_id: str, row: dict) -> str:
    """A step's state when it has no step row: every step of a done unit is
    done; before the cursor done, at the cursor the unit's own state."""
    cursor = row.get("step_id") or ""
    if row["state"] == "done" or (cursor and step_id < cursor):
        return "done"
    return row["state"] if step_id == cursor else ""


def step_bar(row: dict, chips: dict[str, str]) -> list[dict]:
    """One segment per registry step, coloured by that step's own state (its
    work_steps row), else by where the unit's cursor stands."""
    bar = []
    for sid, name in step_names(row["stage"]).items():
        state = chips.get(sid) or cursor_state(sid, row)
        css = STEP_CSS.get(state) or (colour_class(state) if state else "none")
        bar.append({"id": sid, "name": name, "state": state or "not yet", "css": css})
    return bar


def step_states(conn: sqlite3.Connection, order_ids: list[int]) -> dict[int, dict[str, str]]:
    """{order_id: {step_id: state}} for every row shown, in one query."""
    out: dict[int, dict[str, str]] = {i: {} for i in order_ids}
    if not order_ids:
        return out
    marks = ",".join("?" * len(order_ids))
    for r in conn.execute(f"SELECT order_id, step_id, state FROM work_steps WHERE order_id IN ({marks})",
                          order_ids):
        out[r["order_id"]][r["step_id"]] = r["state"]
    return out


def gate_label(gate: str) -> str:
    """A gate's column head: `EYE_PANELS` reads `panels`."""
    return gate.removeprefix("EYE_").lower()


def book_groups(rows: list[dict], names: dict[str, str]) -> list[dict]:
    """The rows under their book, each book in its rows' order; the book whose
    first row needs the most attention leads."""
    groups: dict[str, dict] = {}
    for r in rows:
        g = groups.setdefault(r["codex_id"], {"codex_id": r["codex_id"], "rows": [], "done": 0,
                                               "name": names.get(r["codex_id"], r["codex_id"])})
        g["rows"].append(r)
        g["done"] += r["shown"] in ("done", "flagged")
    for g in groups.values():
        g["total"] = len(g["rows"])
        g["rank"] = min(rank(r) for r in g["rows"])
    return sorted(groups.values(), key=lambda g: g["rank"])


def dress(row: dict, chips: dict[str, str], gates: list[str]) -> dict:
    """A shown row with everything the glance needs."""
    row["strip"] = verdict_strip(row["verdicts"], gates)
    row["gate_labels"] = [gate_label(c["gate"]) for c in row["strip"]]
    row["bar"] = step_bar(row, chips)
    row["ago"], row["gpu_h"] = ago(row.get("updated_at")), gpu_hours(row.get("gpu_seconds"))
    return row


# --- a department ---


def department(conn: sqlite3.Connection, stage: str, book: str | None = None,
               state: str | None = None) -> dict:
    """The department's table: its rows in attention order, each with its
    verdict strip; filtered by book and shown state when asked.  A stage the
    registry does not know raises ValueError (db.department_rows)."""
    rows = sorted((row_view(r) for r in db.department_rows(conn, stage)), key=rank)
    gates = gate_order(stage)
    names = book_names(conn)
    counts = Counter(r["shown"] for r in rows)
    kept = [r for r in rows if (not book or r["codex_id"] == book) and (not state or r["shown"] == state)]
    chips = step_states(conn, [r["id"] for r in kept])
    kept = [dress(r, chips[r["id"]], gates) for r in kept]
    return {"stage": stage, "rows": kept, "gates": gates, "counts": dict(counts),
            "gate_labels": [gate_label(g) for g in gates], "groups": book_groups(kept, names),
            "books": {c: names.get(c, c) for c in sorted({r["codex_id"] for r in rows})}}


# --- a unit ---


def step_chip(entry: dict, chip: dict | None) -> dict:
    """A step's chip: the registry row's id and name over the work_steps row
    when there is one, else a queued chip with nothing on it."""
    d = {"step_id": entry["id"], "name": entry.get("name", ""), "state": "queued", "attempt": 0,
         "run_id": None, "started_at": None, "ended_at": None, "seconds": 0.0, "verdict_by": None,
         "verdict_word": None, "verdict_path": None, "terminal": "", "detail": None}
    if chip:
        d.update({k: chip[k] for k in chip if k in d})
    d["glyph"], d["css"] = glyph(d["state"]), colour_class(d["state"])
    return d


def unit_steps(conn: sqlite3.Connection, order_id: int, stage: str) -> list[dict]:
    """The unit's chips in registry order; a stage the registry does not know
    lists the chips it has, by id."""
    chips = {r["step_id"]: dict(r) for r in conn.execute(
        "SELECT * FROM work_steps WHERE order_id = ? ORDER BY step_id", (order_id,))}
    try:
        entries = registry.steps(stage)
    except ValueError:
        entries = [{"id": sid, "name": ""} for sid in chips]
    return [step_chip(entry, chips.get(entry["id"])) for entry in entries]


def tail_lines(path: Path, limit_bytes: int = TAIL_BYTES) -> list[str]:
    """The file's last lines within a byte budget; a line cut by the budget is
    dropped; [] for a file that is not there."""
    path = Path(path)
    if not path.is_file():
        return []
    size = path.stat().st_size
    with open(path, "rb") as fh:
        fh.seek(max(0, size - limit_bytes))
        text = fh.read().decode("utf-8", errors="replace")
    lines = text.splitlines()
    if size > limit_bytes and lines:
        lines = lines[1:]
    return [line for line in lines if line.strip()]


def parse_jsonl(lines: list[str]) -> list[dict]:
    """Each line as a dict; a line that is not JSON is kept as {'raw': line}."""
    out = []
    for line in lines:
        try:
            doc = json.loads(line)
        except ValueError:
            doc = {"raw": line}
        out.append(doc if isinstance(doc, dict) else {"raw": line})
    return out


def learnings_tail(home: Path | None, n: int = 8) -> list[dict]:
    """The last n rows of <home>/learnings.jsonl."""
    if home is None:
        return []
    return parse_jsonl(tail_lines(Path(home) / "learnings.jsonl")[-n:])


def timing_rows(home: Path | None) -> list[dict]:
    """Every row of <home>/timing.jsonl, in the order written."""
    if home is None:
        return []
    return parse_jsonl(tail_lines(Path(home) / "timing.jsonl", limit_bytes=4 * TAIL_BYTES))


def log_tail(folder: Path, run_id: str | None, n: int = 20) -> tuple[str | None, list[dict]]:
    """(name, rows): the last n WARNING+ lines of the newest log in the stage's
    folder whose name carries the run_id -- else the newest log at all."""
    folder = Path(folder)
    files = sorted(folder.glob("*.log"), key=lambda p: (p.stat().st_mtime, p.name)) if folder.is_dir() else []
    hits = [f for f in files if run_id and run_id in f.name] or files
    if not hits:
        return None, []
    newest = hits[-1]
    rows = [r for r in parse_jsonl(tail_lines(newest)) if r.get("level") in LOG_LEVELS]
    return newest.name, rows[-n:]


def thumbnails(home: Path, stage: str, codex_id: str) -> list[dict]:
    """The pictures the steps already wrote under the unit's home, by a fixed
    allowlist per stage; the master is the newest iteration only."""
    out = []
    for kind, pattern in THUMBS.get(stage, ()):
        hits = sorted(Path(home).glob(pattern), key=lambda p: p.name)
        if kind == "master" and hits:
            hits = [max(hits, key=lambda p: (p.stat().st_mtime, p.name))]
        for hit in hits:
            rel = library_paths.book_relative(hit, codex_id)
            if rel:
                out.append({"kind": kind, "rel": rel, "url": library_paths.artefact_url(codex_id, rel),
                            "thumb": strip_thumb(codex_id, rel, hit)})
    return out


def strip_thumb(codex_id: str, rel: str, hit: Path) -> str | None:
    """The small WebP a picture is drawn with; None for a video."""
    if hit.suffix.lower() not in thumbs.IMAGES:
        return None
    return library_paths.thumb_url(codex_id, rel, 320, library_paths.stamp(hit))


def deliverable(book: Path | None, codex_id: str, rel: str | None) -> dict | None:
    """The row's deliverable as a link, saying whether the file is on disk."""
    if not rel:
        return None
    exists = bool(book) and (Path(book) / rel).is_file()
    return {"rel": rel, "exists": exists,
            "url": library_paths.artefact_url(codex_id, rel) if exists else None}


def unit(conn: sqlite3.Connection, library: Path, codex_id: str, stage: str, unit: str,
         logs: Path | None = None) -> dict | None:
    """The unit opened: its row, chips, verdicts, deliverable, thumbnails, the
    learnings and log tails, the timing rows; None when it has no row."""
    row = db.work_order(conn, codex_id, stage, unit)
    if row is None:
        return None
    r = row_view(row)
    book = library_paths.book_folder(library, codex_id)
    home = book / r["home"] if book else None
    log_name, log = log_tail(Path(logs or Path(library).parent / "logs") / codex_id / stage, r["run_id"])
    return {"row": r, "steps": unit_steps(conn, r["id"], stage),
            "verdicts": verdict_strip(r["verdicts"], gate_order(stage)),
            "deliverable": deliverable(book, codex_id, r["deliverable"]),
            "thumbnails": thumbnails(home, stage, codex_id) if home else [],
            "learnings": learnings_tail(home), "log_name": log_name, "log": log,
            "timing": timing_rows(home), "running": r["state"] == "running",
            "book_name": book_names(conn).get(codex_id, codex_id)}


# --- a book ---


def published_source(conn: sqlite3.Connection, book: Path | None, codex_id: str, unit: str) -> str | None:
    """Where the unit's publication is known from: a done `publish` row, else
    the unit's youtube.json on disk; None when neither."""
    row = db.work_order(conn, codex_id, "publish", unit)
    if row is not None and row["state"] == "done":
        return "row"
    if book and (Path(book) / "episodes" / unit / "youtube.json").is_file():
        return "file"
    return None


def book(conn: sqlite3.Connection, library: Path, codex_id: str) -> dict | None:
    """The book down every department: units across, stages down, a glyph per
    cell, the published row with its source, the GPU total."""
    name = book_names(conn).get(codex_id)
    if name is None:
        return None
    rows = [row_view(r) for r in conn.execute(
        "SELECT * FROM work_orders WHERE codex_id = ? ORDER BY stage, sequence, unit", (codex_id,))]
    stages = registry.stage_names() + sorted({r["stage"] for r in rows} - set(registry.stage_names()))
    chapters = {r["unit"] for r in rows if r["kind"] != "book"}
    units = sorted({r["unit"] for r in rows}, key=lambda u: (u in chapters, u))
    cells: dict[str, dict] = {s: {} for s in stages}
    for r in rows:
        cells[r["stage"]][r["unit"]] = {"glyph": r["glyph"], "css": r["css"], "state": r["shown"], "step_id": r["step_id"]}
    folder = library_paths.book_folder(library, codex_id)
    published = {u: src for u in units if (src := published_source(conn, folder, codex_id, u))}
    return {"codex_id": codex_id, "name": name, "stages": stages, "units": units, "cells": cells,
            "published": published, "gpu_seconds": sum(r["gpu_seconds"] or 0 for r in rows),
            "holds": [h for h in holds(conn) if h["codex_id"] in (None, codex_id)]}
