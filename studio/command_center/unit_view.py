"""The unit page's bands (research F, the redesign; research G, the data): one
question per band -- where is it (head + step bar), is it looping (health),
which gate holds it and on what (gates), what does it look like (pictures,
master), what can I do (actions, orders), and the raw rows behind a fold.

Reads only, and only under the unit's own book folder (every file goes through
`library_paths.resolve_artefact`).  `views.unit` gives the row, chips, strip and
tails; this module adds the bands by composing `unit_parse` over the events
rows, the learnings, the timing rows, the run's log and the files the verdict
row names -- the live verdict is the path the row's `verdicts[gate]` names, never a glob."""
from __future__ import annotations

import json
import sqlite3
from collections import Counter
from datetime import datetime, timezone, tzinfo
from pathlib import Path

from studio import manifest
from studio.command_center import library_paths, views
from studio.command_center import unit_parse as up

PICTURES = {"episode": {"plan": "plan.json", "panels": "storyboard/shot_*.png", "panel_gate": "EYE_PANELS",
                        "dq": "storyboard/panel_dq.json", "takes": "takes/r2v/T*.mp4", "take_gate": "EYE_TAKES",
                        "qc": "qc_r2v.json", "masters": "cut/master*.mp4", "published": "youtube.json",
                        "contact": "storyboard/contact.png"}}
HOW_CSS = {"completed": "green", "failed": "red", "deferred": "purple", "running": "blue", "killed": "grey"}
READ_BYTES = 512 * 1024
FAULT_ITEMS = 40


# --- reads ---


def read_doc(library: Path, codex: str, rel: str | None):
    """A book file's JSON, or None: off the book, missing, or not JSON."""
    target = library_paths.resolve_artefact(library, codex, rel) if rel else None
    if target is None:
        return None
    try:
        return json.loads(target.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def jsonl(path: Path | None, limit_bytes: int = READ_BYTES) -> list[dict]:
    """A JSONL file's rows within a byte budget; a line that is not JSON is a raw row."""
    return views.parse_jsonl(views.tail_lines(path, limit_bytes)) if path else []


def unit_events(conn: sqlite3.Connection, codex: str, stage: str, unit: str) -> list[dict]:
    """The unit's events in the order written -- by unit, not order_id (older rows lack it)."""
    return [dict(r) for r in conn.execute(
        "SELECT event_ts, step_id, event, run_id, detail FROM events"
        " WHERE codex_id = ? AND stage = ? AND unit = ? ORDER BY id", (codex, stage, unit))]


def unit_orders(conn: sqlite3.Connection, codex: str, stage: str, unit: str, n: int = 5) -> list[dict]:
    """This unit's last n orders, newest first, with who took each (or `pending`)."""
    rows = conn.execute("SELECT * FROM orders WHERE codex_id = ? AND stage = ? AND unit = ?"
                        " ORDER BY id DESC LIMIT ?", (codex, stage, unit, n))
    return [{**dict(r), "taken": views.order_taken(r)} for r in rows]


def unit_hold(conn: sqlite3.Connection, codex: str, stage: str, unit: str) -> dict | None:
    """The open hold on this very unit, if any."""
    hits = [h for h in views.holds(conn) if (h["codex_id"], h["stage"], h["unit"]) == (codex, stage, unit)]
    return hits[0] if hits else None


def log_file(logs: Path, codex: str, stage: str, name: str | None) -> Path | None:
    """The run's log that views.unit chose, as a path under the logs root."""
    return Path(logs) / codex / stage / name if name else None


def worth_showing(row: dict) -> bool:
    """A log row the page keeps: WARNING and above, or a ladder's climb."""
    return row.get("level") in views.LOG_LEVELS or row.get("step_id") == "ladders" or "raw" in row


# --- format ---


def span(seconds) -> str:
    """`1h42` / `18m` / `40s` / `` for a number of seconds."""
    s = int(seconds or 0)
    if s >= 3600:
        return f"{s // 3600}h{(s % 3600) // 60:02d}"
    return f"{s // 60}m" if s >= 60 else (f"{s}s" if s else "")


def hhmm(ts) -> str:
    """`04:02` from an ISO stamp (UTC); '' for junk."""
    d = up.parse_ts(ts) if ts else None
    return d.strftime("%H:%M") if d else ""


def day_hhmm(ts) -> str:
    """`27 Sep 04:02` from an ISO stamp (UTC)."""
    d = up.parse_ts(ts) if ts else None
    return d.strftime("%d %b %H:%M") if d else ""


# --- band 1: the head ---


def lease(row: dict, now: datetime) -> dict:
    """Whether a running row's lease is alive: ok to hh:mm, stale since, or none."""
    until = up.parse_ts(row.get("lease_until")) if row.get("lease_until") else None
    if row["state"] != "running" or until is None:
        return {"state": "none", "until": ""}
    return {"state": "ok" if until >= now else "stale", "until": until.strftime("%H:%M")}


def head_band(row: dict, plan: dict | None, now: datetime) -> dict:
    """Who the unit is and where it stands: plan title and question, lease, run, time."""
    plan = plan if isinstance(plan, dict) else {}
    return {"title": str(plan.get("title") or ""), "question": up.clip(plan.get("question")),
            "lease": lease(row, now), "run_short": _run_short(row),
            "moved": views.ago(row.get("updated_at")), "gpu_h": views.gpu_hours(row.get("gpu_seconds")),
            "started": day_hhmm(row.get("started_at")), "finished": day_hhmm(row.get("finished_at"))}


def _run_short(row: dict) -> str:
    """A run id's clock (`04:02`) from its trailing stamp; the full id stays in title=."""
    rid = str(row.get("run_id") or "")
    tail = rid.rsplit("__", 1)[-1]
    return f"{tail[8:10]}:{tail[10:12]}" if len(tail) == 14 and tail.isdigit() else rid[-8:]


# --- band 2: the step bar ---


def chip_state(chip: dict, row: dict) -> dict:
    """A chip with no step row of its own reads the unit's cursor (a finished unit's steps are done)."""
    if chip["state"] != "queued" or chip.get("run_id") or chip.get("ended_at"):
        return chip
    state = views.cursor_state(chip["step_id"], row)
    return {**chip, "state": state, "glyph": views.glyph(state), "css": views.colour_class(state)} if state else chip


def step_band(chips: list[dict], row: dict, events: list[dict], timing: list[dict],
              now: datetime, tz: tzinfo | None) -> list[dict]:
    """One segment per step: its chip, the last window's wall time, the ≈ script
    seconds, and the one-line reason a failed or deferred step left."""
    times = {t["id"]: t for t in up.step_timing([{"id": c["step_id"]} for c in chips], events, timing, now, tz)}
    out = []
    for c in (chip_state(c, row) for c in chips):
        t = times.get(c["step_id"], {})
        out.append({**c, "css": views.STEP_CSS.get(c["state"]) or c["css"], "runs": t.get("runs", 0),
                    "wall": span(t.get("last_wall_s")) + ("…" if t.get("open") else ""),
                    "script": span(t.get("total_s")), "reason": up.clip(c.get("detail")) if c["state"] in
                    ("failed", "deferred", "escalated") else "", "cur": c["step_id"] == row.get("step_id")})
    return out


# --- band 3: health ---


def pass_rows(rows: list[dict]) -> list[dict]:
    """Each pass with its colour, its clock and its one-word label."""
    return [{**p, "css": HOW_CSS.get(p["how"], "grey"), "at": hhmm(p["started"]), "day": day_hhmm(p["started"]),
             "wall": span(p["wall_s"]), "label": f"{p['ended_on']} {p['reason']}"} for p in rows]


def health_band(rows: list[dict], learnings: list[dict], finished: bool) -> dict:
    """Looping or improving: the pass timeline, the loop detector, the gates'
    measured series, how passes ended, and the plan titles drafted."""
    titles = up.plan_titles(learnings)
    return {"passes": pass_rows(rows), "loop": up.loop_state(rows), "trend": up.gate_trend(learnings, rows),
            "ended": up.ended_on_counts(rows), "titles": titles, "drift": len(titles) > 1,
            "finished": finished, "n": len(rows)}


# --- band 4: gates ---


def gate_steps(stage: str) -> dict[str, str]:
    """{gate: the step answerable for it} from manifest.VERDICTS."""
    return {gate: step for gate, step, _ in manifest.VERDICTS.get(stage, ())}


def gate_block(chip: dict, doc, step: str) -> dict:
    """One gate: its chip, its step, and the file's faults grouped by kind."""
    doc = doc if isinstance(doc, dict) else {}
    signed = doc.get("signed_at") or doc.get("reviewed_at") or ""
    return {**chip, "step": step, "kinds": up.fault_kinds(doc), "signed": hhmm(signed),
            "shots": up.shot_faults(doc), "read": bool(doc)}


def gate_band(library: Path, codex: str, stage: str, chips: list[dict]) -> list[dict]:
    """Every gate in order; a signed gate reads the file its row names."""
    steps = gate_steps(stage)
    return [gate_block(c, read_doc(library, codex, c["path"]) if c["path"] else None, steps.get(c["gate"], ""))
            for c in chips]


# --- band 5: pictures ---


def book_files(book: Path | None, home: Path | None, pattern: str | None) -> list[str]:
    """Book-relative paths of the unit's files matching a pattern, by name."""
    if not (book and home and pattern and Path(home).is_dir()):
        return []
    return [p.relative_to(book).as_posix() for p in sorted(Path(home).glob(pattern), key=lambda p: p.name)]


def dq_flags(dq) -> dict[int, list[str]]:
    """{shot: flags} from panel_dq.json rows (a list keyed by `shot`)."""
    out: dict[int, list[str]] = {}
    for r in dq if isinstance(dq, list) else []:
        if isinstance(r, dict) and isinstance(r.get("shot"), int) and r.get("flags"):
            out[r["shot"]] = [str(f) for f in r["flags"]]
    return out


def tile(codex: str, rel: str, plan: dict, faults: list[dict], dq: list[str], prefix: str) -> dict:
    """A picture tile: its shot's plan row, its fault badges, its dq flags."""
    shot = up.panel_shot(rel, plan) or {}
    n = shot.get("index", up.shot_key(Path(rel).stem))
    return {"rel": rel, "url": library_paths.artefact_url(codex, rel), "index": n,
            "label": f"{prefix}{n:02d}" if isinstance(n, int) else str(n),
            "section": str(shot.get("section") or ""), "size": str(shot.get("size") or ""),
            "frame": str(shot.get("frame") or ""), "motion": str(shot.get("motion") or ""),
            "camera": str(shot.get("camera") or ""), "faults": faults, "dq": dq,
            "flagged": bool(faults)}


def tiles(codex: str, rels: list[str], plan: dict, gate: dict | None, dq: dict, prefix: str) -> list[dict]:
    """Tiles for a set of pictures, badged by the gate that names their shots."""
    shots = (gate or {}).get("shots") or {}
    out = []
    for rel in rels:
        shot = up.panel_shot(rel, plan) or {}
        n = shot.get("index", up.shot_key(Path(rel).stem))
        out.append(tile(codex, rel, plan, shots.get(n, []), dq.get(n, []), prefix))
    return out


def slots(plan: dict, reason: str) -> list[dict]:
    """One grey slot per planned shot, before any take exists."""
    shots = [s for s in (plan or {}).get("shots") or [] if isinstance(s, dict)]
    return [{"label": f"T{int(s['index']):02d}" if str(s.get("index", "")).isdigit() else str(s.get("index")),
             "reason": reason} for s in shots]


def pictures_band(library: Path, codex: str, stage: str, book: Path | None, home: Path | None,
                  plan: dict, gates: list[dict], steps: list[dict]) -> dict:
    """Panels and takes as tiles (badged by their gates), or slots while no take exists."""
    cfg = PICTURES.get(stage)
    if not cfg:
        return {"panels": [], "takes": [], "slots": [], "wait": "", "flagged": 0, "contact": None,
                "panel_step": "", "take_step": ""}
    by = {g["gate"]: g for g in gates}
    dq = dq_flags(read_doc(library, codex, _rel(book, home, cfg["dq"])))
    panels = tiles(codex, book_files(book, home, cfg["panels"]), plan, by.get(cfg["panel_gate"]), dq, "")
    takes = tiles(codex, book_files(book, home, cfg["takes"]), plan, by.get(cfg["take_gate"]), {}, "T")
    posters = {p["index"]: p["url"] for p in panels}
    takes = [{**t, "poster": posters.get(t["index"], "")} for t in takes]
    wait = "" if takes else take_wait(steps)
    answer = gate_steps(stage)
    return {"panels": panels, "takes": takes, "slots": [] if takes else slots(plan, wait), "wait": wait,
            "flagged": sum(t["flagged"] for t in panels), "contact": _rel_if(book, home, cfg["contact"]),
            "panel_step": answer.get(cfg["panel_gate"], ""), "take_step": answer.get(cfg["take_gate"], "")}


def take_wait(steps: list[dict]) -> str:
    """Why there are no takes: the shooting step's own reason, else not reached."""
    shoot = next((s for s in steps if s.get("reason")), None)
    return f"{shoot['step_id']} {shoot['state']}: {shoot['reason']}" if shoot else "not shot yet"


def _rel(book: Path | None, home: Path | None, name: str) -> str | None:
    return (Path(home) / name).relative_to(book).as_posix() if book and home else None


def _rel_if(book: Path | None, home: Path | None, name: str) -> str | None:
    rel = _rel(book, home, name)
    return rel if rel and (Path(book) / rel).is_file() else None


# --- the master ---


def qc_line(qc: dict) -> dict:
    """The delivered master's measures as the page prints them."""
    lines = [l for l in qc.get("lines") or [] if isinstance(l, dict)]
    return {"seconds": qc.get("seconds"), "planned": qc.get("planned_seconds"), "lufs": qc.get("lufs"),
            "lufs_ok": qc.get("lufs_ok"), "peak": qc.get("true_peak"), "peak_ok": qc.get("tp_ok"),
            "cuts": f"{len(qc.get('planned_cuts') or []) - len(qc.get('missing_cuts') or [])}/"
                    f"{len(qc.get('planned_cuts') or [])}",
            "heard": f"{sum(1 for l in lines if l.get('passed'))}/{len(lines)}"}


def master_band(library: Path, codex: str, stage: str, book: Path | None, home: Path | None,
                thumbs: list[dict]) -> dict | None:
    """The master to play (the QC'd one, else the newest iteration), its QC, the iterations."""
    cfg = PICTURES.get(stage) or {}
    qc = read_doc(library, codex, _rel(book, home, cfg.get("qc", ""))) if cfg else None
    qc = qc if isinstance(qc, dict) else {}
    rel = qc.get("master") if qc.get("master") and book and (Path(book) / qc["master"]).is_file() else None
    rel = rel or next((t["rel"] for t in thumbs if t["kind"] == "master"), None)
    if not rel:
        return None
    iters = [r for r in book_files(book, home, cfg.get("masters")) if r != rel]
    return {"rel": rel, "url": library_paths.artefact_url(codex, rel), "qc": qc_line(qc) if qc else None,
            "iterations": [{"name": Path(r).stem.removeprefix("master_"), "url": library_paths.artefact_url(codex, r)}
                           for r in iters],
            "published": _rel_if(book, home, cfg.get("published", "")) if cfg else None}


# --- band 6: what to do ---


def holding_gate(row: dict, gates: list[dict]) -> dict | None:
    """The gate holding the unit: the one its current step answers for, else the most faults."""
    at_step = [g for g in gates if g["step"] and g["step"] == row.get("step_id") and g["faults"]]
    flagged = sorted((g for g in gates if g["faults"]), key=lambda g: -g["faults"])
    return (at_step or flagged or [None])[0]


def suggest(row: dict, gates: list[dict], stage: str, home_rel: str) -> dict:
    """The redo form's defaults: the holding step, its flagged shots, a note seeded from its faults."""
    gate = holding_gate(row, gates)
    step = (gate or {}).get("step") or row.get("step_id") or ""
    shots = sorted(k for k in (gate or {}).get("shots", {}) if isinstance(k, int))
    kinds = " · ".join(f"{k['kind']} ×{k['n']}" for k in (gate or {}).get("kinds", [])[:4])
    pattern = (PICTURES.get(stage) or {}).get("panels", "") if (gate or {}).get("gate") == "EYE_PANELS" else ""
    art = f"{home_rel}/{pattern.replace('*', f'{shots[0]:02d}')}" if pattern and len(shots) == 1 else ""
    note = f"{gate['gate']}: {kinds}; shots {', '.join(f'{s:02d}' for s in shots)}" if gate and shots else ""
    return {"step_id": step, "shots": shots, "artefact": art, "note": up.clip(note, 300)}


# --- band 7: raw ---


def merged(rows: list[dict]) -> list[dict]:
    """Consecutive learnings with the same (gate, rung) as one row with ×n, newest first."""
    out: list[dict] = []
    for r in rows:
        if out and (out[-1]["gate"], out[-1]["rung"]) == (r["gate"], r["rung"]):
            out[-1] = {**r, "times": out[-1]["times"] + 1}
        else:
            out.append({**r, "times": 1})
    return out[::-1]


def learning_band(rows: list[dict], n: int = 8) -> dict:
    """The learnings as a table: newest n merged rows, each fault list capped; the tallies."""
    parsed = [up.learning_row(r) for r in rows]
    for p in parsed:
        p["more"] = max(0, len(p["faults"]) - FAULT_ITEMS)
        p["faults"] = p["faults"][:FAULT_ITEMS]
        p["at"] = hhmm(p["ts"])
    rows_m = merged(parsed)
    gates = Counter(p["gate"] for p in parsed if p["gate"])
    return {"rows": rows_m[:n], "older": rows_m[n:n + 40], "total": len(parsed), "by_gate": dict(gates.most_common())}


def log_band(rows: list[dict]) -> list[dict]:
    """The run's log rows worth showing, a refusal's items marked new/still/gone, capped."""
    out = up.dedupe_refusals(up.log_rows([r for r in rows if worth_showing(r)]))
    for r in out:
        if r["kind"] == "refusal":
            r["items"] = sorted(r["items"], key=lambda i: i.get("mark") != "new")[:FAULT_ITEMS]
        r["at"] = (r.get("ts") or "")[11:19]
    return out[-30:]


def raw_band(learnings: list[dict], log: list[dict], timing: list[dict], events: list[dict],
             now: datetime, tz: tzinfo | None) -> dict:
    """The collapsed band: learnings table, log lines, timing per stage."""
    return {"learnings": learning_band(learnings), "log": log_band(log),
            "timing": up.timing_by_stage(timing), "timing_n": len(timing),
            "unplaced": up.unplaced(events, timing, now, tz)}


# --- the page ---


def bands(conn: sqlite3.Connection, library: Path, logs: Path, base: dict, codex: str, stage: str,
          now: datetime, tz: tzinfo | None) -> dict:
    """Every band of the unit page from the base view."""
    r = base["row"]
    book = library_paths.book_folder(library, codex)
    home = book / r["home"] if book else None
    events, learnings = unit_events(conn, codex, stage, r["unit"]), jsonl(home / "learnings.jsonl" if home else None)
    plan = read_doc(library, codex, _rel(book, home, (PICTURES.get(stage) or {}).get("plan", "plan.json")))
    plan = plan if isinstance(plan, dict) else {}
    rows = up.passes(events, learnings, base["timing"], r["run_id"] if base["running"] else None, now, tz)
    gates = gate_band(library, codex, stage, base["verdicts"])
    steps = step_band(base["steps"], r, events, base["timing"], now, tz)
    return {"head": head_band(r, plan, now), "bar": steps,
            "health": health_band(rows, learnings, r["shown"] in ("done", "flagged")),
            "gates": gates, "pictures": pictures_band(library, codex, stage, book, home, plan, gates, steps),
            "master": master_band(library, codex, stage, book, home, base["thumbnails"]),
            "orders": unit_orders(conn, codex, stage, r["unit"]), "hold": unit_hold(conn, codex, stage, r["unit"]),
            "suggest": suggest(r, gates, stage, r["home"]),
            "raw": raw_band(learnings, jsonl(log_file(logs, codex, stage, base["log_name"])), base["timing"],
                            events, now, tz)}


def unit(conn: sqlite3.Connection, library: Path, codex: str, stage: str, unit_name: str,
         logs: Path | None = None, now: datetime | None = None, tz: tzinfo | None = None) -> dict | None:
    """The unit opened with every band; None when it has no row."""
    logs = Path(logs or Path(library).parent / "logs")
    base = views.unit(conn, library, codex, stage, unit_name, logs=logs)
    if base is None:
        return None
    return {**base, **bands(conn, library, logs, base, codex, stage, now or datetime.now(timezone.utc), tz)}
