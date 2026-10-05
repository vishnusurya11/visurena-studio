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
import re
import sqlite3
from collections import Counter
from datetime import datetime, timezone, tzinfo
from pathlib import Path

from studio import manifest
from studio.command_center import library_paths, viewer_model, views
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
    return {"title": str(plan.get("title") or ""), "question": up.clip(display_question(plan.get("question"))),
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
    panels = with_thumbs(codex, book, panels)
    posters = {p["index"]: p["thumb"] for p in panels}
    takes = [{**t, "poster": posters.get(t["index"], "")} for t in takes]
    wait = "" if takes else take_wait(steps)
    answer = gate_steps(stage)
    return {"panels": panels, "takes": takes, "slots": [] if takes else slots(plan, wait), "wait": wait,
            "flagged": sum(t["flagged"] for t in panels), "contact": _rel_if(book, home, cfg["contact"]),
            "panel_step": answer.get(cfg["panel_gate"], ""), "take_step": answer.get(cfg["take_gate"], "")}


def with_thumbs(codex: str, book: Path | None, items: list[dict]) -> list[dict]:
    """Picture tiles (120 px) with the versioned `/thumb/` URL they are drawn from."""
    return [{**t, "thumb": library_paths.thumb_url(codex, t["rel"], 120,
                                                   library_paths.stamp(Path(book) / t["rel"]) if book else "")}
            for t in items]


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


# --- truthful media (panel ruling 5.5, 5.6, 5.8) ---


def display_question(q) -> str:
    """The plan's question without its appearance parentheticals ("(grey eyes, …)")."""
    text = re.sub(r"\s*\([^()]*\)", "", str(q or ""))
    return re.sub(r"\s{2,}", " ", text).strip()


def qc_checks(qc: dict) -> list[dict]:
    """The master's five QC measures, each {name, ok, text}."""
    lines = [l for l in qc.get("lines") or [] if isinstance(l, dict)]
    cuts, missing = len(qc.get("planned_cuts") or []), len(qc.get("missing_cuts") or [])
    takes = qc.get("takes") if isinstance(qc.get("takes"), dict) else {}
    heard = sum(1 for l in lines if l.get("passed"))
    return [{"name": "LUFS", "ok": bool(qc.get("lufs_ok")), "text": f"LUFS {qc.get('lufs')}"},
            {"name": "peak", "ok": bool(qc.get("tp_ok")), "text": f"peak {qc.get('true_peak')}"},
            {"name": "cuts", "ok": missing == 0, "text": f"cuts {cuts - missing}/{cuts}"},
            {"name": "lines", "ok": heard == len(lines), "text": f"lines {heard}/{len(lines)}"},
            {"name": "takes", "ok": takes.get("pass") == takes.get("of"),
             "text": f"takes {takes.get('pass', '–')}/{takes.get('of', '–')}"}]


def qc_summary(qc) -> dict | None:
    """`QC 5/5 ✓` when every check passes; the failures in full otherwise; None with no QC."""
    if not isinstance(qc, dict) or not qc:
        return None
    checks = qc_checks(qc)
    fails = [c for c in checks if not c["ok"]]
    return {"n_ok": len(checks) - len(fails), "n": len(checks), "all_ok": not fails, "fails": fails}


def take_poster(home: Path | None, name: str) -> str | None:
    """The take's own first frame (unit-relative), else its middle content frame, else None."""
    for k in (0, 1):
        rel = f"takes/work/content/{name}_{k}.png"
        if home and (Path(home) / rel).is_file():
            return rel
    return None


def master_poster(book: Path | None, unit: str) -> str | None:
    """The publish thumbnail, else the pre-baked title card (the master's first frame)."""
    for rel in (f"publish/{unit}.png", f"title/{unit}.png"):
        if book and (Path(book) / rel).is_file():
            return rel
    return None


def latest_master(home: Path | None) -> dict | None:
    """The newest master file by mtime: its unit-relative path, name and `vN` label."""
    hits = sorted(Path(home).glob("cut/master*.mp4"), key=lambda p: (p.stat().st_mtime, p.name)) if home else []
    if not hits:
        return None
    name = hits[-1].stem.removeprefix("master_")
    n = re.search(r"(\d+)$", name)
    return {"rel": f"cut/{hits[-1].name}", "name": name, "short": f"v{n.group(1)}" if n else name}


def unit_rel(rel: str, home_rel: str) -> str:
    """A book-relative path as the Viewer names it: relative to the unit's home when inside it."""
    prefix = home_rel.rstrip("/") + "/"
    return rel[len(prefix):] if rel.startswith(prefix) else rel


# --- the shot cards: panel and take joined by shot number ---


def take_face(codex: str, book: Path | None, home_rel: str, take: dict) -> dict:
    """The card's main picture for a take: its own frame as the poster, or the reason there is none."""
    name = Path(take["rel"]).stem
    home = Path(book) / home_rel if book else None
    frame = take_poster(home, name)
    poster = library_paths.thumb_url(codex, f"{home_rel}/{frame}", 320,
                                     library_paths.stamp(home / frame)) if frame else ""
    return {"rel": unit_rel(take["rel"], home_rel), "kind": "video", "depth": "take", "poster": poster,
            "why": "" if frame else f"no frame of {name} on disk"}


def panel_face(home_rel: str, panel: dict) -> dict:
    """A panel as a card picture: its thumb and its unit-relative path."""
    return {"rel": unit_rel(panel["rel"], home_rel), "kind": "image", "depth": "panel",
            "poster": panel.get("thumb", ""), "why": ""}


def shot_cards(codex: str, book: Path | None, home_rel: str, panels: list[dict], takes: list[dict]) -> list[dict]:
    """One card per shot number: the take's frame as the main picture, the panel as its inset."""
    by_panel = {p["index"]: p for p in panels}
    by_take = {t["index"]: t for t in takes}
    out = []
    for i in sorted(set(by_panel) | set(by_take), key=lambda k: (not isinstance(k, int), str(k).zfill(4))):
        p, t = by_panel.get(i), by_take.get(i)
        take = take_face(codex, book, home_rel, t) if t else None
        panel = panel_face(home_rel, p) if p else None
        base = p or t
        out.append({"index": i, "label": base["label"].lstrip("T"), "size": base.get("size", ""),
                    "frame": base.get("frame", ""), "take": take, "panel": panel, "main": take or panel,
                    "faults": (p or {}).get("faults", []) + (t or {}).get("faults", []),
                    "dq": (p or {}).get("dq", []), "flagged": bool((p or {}).get("flagged") or (t or {}).get("flagged"))})
    return out


def grid_tiles(codex: str, book: Path | None, home: Path | None) -> list[dict]:
    """The storyboard grids, newest first, each with its setup name and thumb."""
    hits = sorted(Path(home).glob("storyboard/grids/*.png"), key=lambda p: -p.stat().st_mtime) if home else []
    out = []
    for p in hits:
        rel = p.relative_to(home).as_posix()
        name = re.sub(r"^(?:[a-z]+\d+_)?(?:grid_)?", "", p.stem).replace("_", " ")
        out.append({"rel": rel, "name": name, "thumb": library_paths.thumb_url(
            codex, p.relative_to(book).as_posix(), 320, library_paths.stamp(p))})
    return out


# --- the Files section ---


FILE_BUCKETS = (("Plan and verdicts", None), ("Storyboard", "storyboard/"), ("Takes", "takes/"),
                ("Master", ("cut/", "review/")), ("Audio", "audio/"), ("Reports", "reports/"),
                ("Run records and logs", None))
FILE_SETS = (("storyboard/shot_", "shots"), ("storyboard/grids/", "grids"), ("takes/r2v/T", "takes"),
             ("cut/master", "masters"))


def file_pattern(rel: str) -> str:
    """The name with every short counter (1-3 digits, not inside a hex hash or a stamp) as N's."""
    return re.sub(r"(?<![0-9A-Fa-f])\d{1,3}(?![0-9A-Fa-f])", lambda m: "N" * len(m.group()), rel)


def file_bucket(rel: str) -> str:
    """The Files group a unit-relative path belongs to."""
    for name, prefix in FILE_BUCKETS:
        if prefix and rel.startswith(prefix):
            return name
    return "Run records and logs" if rel.startswith("_logs/") or rel.endswith((".jsonl", ".log")) \
        else "Plan and verdicts"


def file_set(rel: str) -> str:
    """The Viewer sequence a file opens in."""
    return next((s for prefix, s in FILE_SETS if rel.startswith(prefix)), "files")


DIR_FOLD = 6


def fold_folder(rel: str) -> str:
    """The folder a deep file may fold into: its first two path parts (`storyboard/grids`), '' when shallower."""
    parts = rel.split("/")
    return "/".join(parts[:2]) if len(parts) >= 3 else ""


def file_keys(files: list[dict]) -> dict[str, list[dict]]:
    """Files by fold key: a second-level folder with more than DIR_FOLD names folds whole, else by name pattern."""
    per_dir: dict[str, set] = {}
    for f in files:
        per_dir.setdefault(fold_folder(f["rel"]), set()).add(file_pattern(f["rel"]))
    by: dict[str, list[dict]] = {}
    for f in files:
        folder = fold_folder(f["rel"])
        key = f"{folder}/…" if folder and len(per_dir[folder]) > DIR_FOLD else file_pattern(f["rel"])
        by.setdefault(key, []).append(f)
    return by


def file_rows(files: list[dict]) -> list[dict]:
    """One row per file, three or more files of one name pattern (or a crowded folder) folded into a counted row."""
    by = file_keys(files)
    rows = []
    for pattern, fs in by.items():
        many = len(fs) >= 3
        rows.append({"label": pattern if many else fs[0]["rel"], "n": len(fs), "rel": fs[0]["rel"],
                     "set": file_set(fs[0]["rel"]), "kind": fs[0].get("kind") or "doc",
                     "size": vm_size(sum(int(f.get("size") or 0) for f in fs))})
    return rows


def file_groups(files: list[dict]) -> list[dict]:
    """The unit folder by kind, in a fixed order, empty groups left out."""
    groups = {name: [] for name, _ in FILE_BUCKETS}
    for f in files:
        groups[file_bucket(f["rel"])].append(f)
    return [{"name": name, "rows": file_rows(fs), "n": len(fs)} for name, fs in groups.items() if fs]


def vm_size(n: int) -> str:
    """Bytes as `3.0 KB` / `31.9 MB` (the Viewer's own format)."""
    return viewer_model.size(n)


def unit_files(home: Path | None, logs: list[dict]) -> dict:
    """The Files section: the unit folder's viewable files and the run logs, grouped."""
    files = viewer_model.index_files(home) if home and Path(home).is_dir() else []
    files += [{"rel": x["rel"], "size": x.get("size", 0), "kind": "log"} for x in logs]
    return {"groups": file_groups(files), "n": len(files),
            "size": vm_size(sum(int(f.get("size") or 0) for f in files))}


# --- the sibling units and the gate word ---


def natural(name: str) -> tuple:
    """`ep9` before `ep10`: digit runs compare as numbers."""
    return tuple(int(t) if t.isdigit() else t for t in re.split(r"(\d+)", name))


def siblings(conn: sqlite3.Connection, codex: str, stage: str, unit: str) -> dict:
    """The units before and after this one in this book's department, in natural name order."""
    names = sorted((r[0] for r in conn.execute("SELECT unit FROM work_orders WHERE codex_id = ? AND stage = ?",
                                               (codex, stage))), key=natural)
    if unit not in names:
        return {"prev": None, "next": None}
    k = names.index(unit)
    return {"prev": names[k - 1] if k > 0 else None, "next": names[k + 1] if k + 1 < len(names) else None}


GATE_WORDS = {"amber": "flagged", "green": "passed", "purple": "deferred", "red": "failed"}


def gate_state(chip: dict) -> str:
    """One state word per gate: not signed, flagged, passed, deferred or failed."""
    if not (chip.get("by") or chip.get("word")):
        return "not signed"
    return GATE_WORDS.get(chip.get("css"), "failed")


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
    gates = [{**g, "state": gate_state(g)} for g in gate_band(library, codex, stage, base["verdicts"])]
    steps = step_band(base["steps"], r, events, base["timing"], now, tz)
    pics = media_band(codex, book, home, r["home"],
                      pictures_band(library, codex, stage, book, home, plan, gates, steps))
    return {"head": {**head_band(r, plan, now),
                     "latest": latest_master(home)}, "bar": steps,
            "health": health_band(rows, learnings, r["shown"] in ("done", "flagged")),
            "gates": gates, "pictures": pics,
            "master": screen_band(library, codex, stage, book, home, r["unit"], base["thumbnails"]),
            "orders": unit_orders(conn, codex, stage, r["unit"]), "hold": unit_hold(conn, codex, stage, r["unit"]),
            "suggest": suggest(r, gates, stage, r["home"]),
            "siblings": siblings(conn, codex, stage, r["unit"]),
            "files": unit_files(home, viewer_model.run_logs(logs, codex, stage, run_ids(events))),
            "raw": raw_band(learnings, jsonl(log_file(logs, codex, stage, base["log_name"])), base["timing"],
                            events, now, tz)}


def run_ids(events: list[dict]) -> list[str]:
    """The unit's run ids in the order they first appear."""
    return list(dict.fromkeys(e["run_id"] for e in events if e.get("run_id")))


def media_band(codex: str, book: Path | None, home: Path | None, home_rel: str, pics: dict) -> dict:
    """The pictures band plus the shot cards and the grids the page draws."""
    return {**pics, "cards": shot_cards(codex, book, home_rel, pics["panels"], pics["takes"]),
            "grids": grid_tiles(codex, book, home), "home": home_rel}


def screen_band(library: Path, codex: str, stage: str, book: Path | None, home: Path | None,
                unit_name: str, thumbs: list[dict]) -> dict | None:
    """The master band plus what the screening room draws: poster, QC summary, unit-relative path."""
    m = master_band(library, codex, stage, book, home, thumbs)
    if m is None:
        return None
    qc = read_doc(library, codex, _rel(book, home, (PICTURES.get(stage) or {}).get("qc", ""))) if home else None
    poster = master_poster(book, unit_name)
    return {**m, "summary": qc_summary(qc), "sha8": (qc or {}).get("sha8", "") if isinstance(qc, dict) else "",
            "vrel": unit_rel(m["rel"], Path(home).relative_to(book).as_posix()) if book and home else m["rel"],
            "poster": master_poster_url(codex, book, poster)}


def master_poster_url(codex: str, book: Path | None, poster: str | None) -> str:
    """The screening room's poster: the 1024 WebP of the publish thumbnail ("" when there is none)."""
    if not poster or book is None:
        return ""
    return library_paths.thumb_url(codex, poster, 1024, library_paths.stamp(Path(book) / poster))


def unit(conn: sqlite3.Connection, library: Path, codex: str, stage: str, unit_name: str,
         logs: Path | None = None, now: datetime | None = None, tz: tzinfo | None = None) -> dict | None:
    """The unit opened with every band; None when it has no row."""
    logs = Path(logs or Path(library).parent / "logs")
    base = views.unit(conn, library, codex, stage, unit_name, logs=logs)
    if base is None:
        return None
    return {**base, **bands(conn, library, logs, base, codex, stage, now or datetime.now(timezone.utc), tz)}
