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

from studio import db, gate_policy, registry
from studio.command_center import library_paths

GLYPHS = {"queued": "○", "blocked": "◌", "running": "●", "done": "✓", "flagged": "⚑",
          "deferred": "↩", "failed": "✕", "escalated": "✋", "held": "⏸", "stale": "~",
          "skipped": "–"}
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


# --- the vocabulary ---


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


def row_view(row: sqlite3.Row | dict) -> dict:
    """A work-order row as the templates read it: the columns, the verdicts
    JSON parsed, the shown state, its glyph and colour, the step's name."""
    r = dict(row)
    r["verdicts"] = json.loads(r["verdicts"]) if r.get("verdicts") else {}
    r["shown"] = display_state(r["state"], r.get("flags") or 0)
    r["glyph"] = glyph(r["state"], r.get("flags") or 0)
    r["css"] = colour_class(r["shown"])
    r["step_name"] = step_names(r["stage"]).get(r.get("step_id") or "", "")
    r["elapsed"] = elapsed(r.get("started_at")) if r["state"] == "running" else ""
    return r


def book_names(conn: sqlite3.Connection) -> dict[str, str]:
    """{codex_id: name} for the breadcrumbs."""
    return {r["id"]: r["name"] for r in conn.execute("SELECT id, name FROM codex")}


# --- the home and the floor ---


def floor(conn: sqlite3.Connection) -> dict:
    """On the floor: the running rows (the GPU's first) and the next four of
    the queue, in the order a runner would take them."""
    running = [row_view(r) for r in conn.execute(
        "SELECT * FROM work_orders WHERE state = 'running' ORDER BY gpu DESC, started_at, id")]
    nxt = [row_view(r) for r in conn.execute("SELECT * FROM v_queue LIMIT 4")]
    return {"running": running, "next": nxt}


def queue(conn: sqlite3.Connection) -> list[dict]:
    """The whole queue, derived: priority, slate order, unit (v_queue)."""
    return [row_view(r) for r in conn.execute("SELECT * FROM v_queue")]


def attention(conn: sqlite3.Connection) -> list[dict]:
    """Needs you: failed, deferred, escalated, stale -- oldest first, each with
    the detail its current step left."""
    rows = conn.execute(
        "SELECT w.*, (SELECT s.detail FROM work_steps s WHERE s.order_id = w.id"
        " AND s.step_id = w.step_id) AS detail FROM v_attention w ORDER BY w.updated_at, w.id")
    return [row_view(r) for r in rows]


def holds(conn: sqlite3.Connection) -> list[dict]:
    """Every open hold, oldest first."""
    return [dict(r) for r in conn.execute("SELECT * FROM holds WHERE lifted_at IS NULL ORDER BY id")]


def lane(conn: sqlite3.Connection, stage: str) -> dict:
    """One department's lane: the count, counts by shown state, the glyph
    tally in attention order, and the six rows that matter most."""
    rows = sorted((row_view(r) for r in db.department_rows(conn, stage)), key=rank)
    counts = Counter(r["shown"] for r in rows)
    tally = [(GLYPHS[s], counts[s]) for s in ATTENTION if counts.get(s)]
    return {"stage": stage, "total": len(rows), "counts": dict(counts), "tally": tally,
            "bar": [r["css"] for r in rows], "rows": rows[:6]}


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
    out = []
    for r in rows:
        d = dict(r)
        d["step_name"] = step_names(d["stage"]).get(d["step_id"], "")
        d["glyph"], d["css"] = glyph(d["state"]), colour_class(d["state"])
        out.append(d)
    return out


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
    for r in kept:
        r["strip"] = verdict_strip(r["verdicts"], gates)
    return {"stage": stage, "rows": kept, "gates": gates, "counts": dict(counts),
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
                out.append({"kind": kind, "rel": rel, "url": library_paths.artefact_url(codex_id, rel)})
    return out


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
