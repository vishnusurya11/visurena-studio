"""The Viewer's unit model (SPEC_v3 "one Viewer = a sequence + a position + a
renderer per kind"; V03 the file inventory and provenance edges; V06 the
provenance panel).  `unit_model(folder, unit, ...)` answers what the Viewer
walks for one unit: the viewable files (unit-relative, with size and mtime),
the run logs, and five sequences -- Shots (panel -> staged -> take -> master
segment), Takes (kept -> failed attempts), Grids (current -> superseded draws),
Masters (iterations folded by equal bytes) and Files (the known docs, then the
logs).  Every join is one key from V03 §2; a link with no key is said
("not rendered yet", "no take card"), never guessed.  Pure reads under the
unit's folder; the route resolves and guards the folder."""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, tzinfo
from pathlib import Path, PurePosixPath

FPS = 24
DOC_CAP = 2 * 1024 * 1024
FILE_CAP = 6000
KINDS = {".png": "image", ".jpg": "image", ".jpeg": "image", ".webp": "image", ".mp4": "video",
         ".wav": "audio", ".json": "doc", ".jsonl": "doc", ".txt": "text", ".md": "text", ".log": "log"}
SKIP_DIRS = frozenset({"__pycache__", ".git"})
DOCS = {"plan": "plan.json", "pv": "plan.verdict.json", "layout": "storyboard/layout.json",
        "cards": "takes/r2v/prompts.json", "ran": "takes/r2v/shots.json", "stills": "takes/r2v/stills.json",
        "qc": "qc_r2v.json"}
EYE = re.compile(r"^(storyboard|takes/r2v|review)/eye_[0-9a-f]+\.json$")
EYE_GROUP = {"storyboard": "panel", "takes": "take", "review": "master"}
FILE_ORDER = ["plan.json", "plan.verdict.json", "storyboard/layout.json", "storyboard/panel_dq.json",
              "storyboard/panel_content.json", re.compile(r"^storyboard/eye_"), "takes/r2v/prompts.json",
              "takes/r2v/shots.json", "takes/r2v/stills.json", re.compile(r"^takes/r2v/eye_"), "qc_r2v.json",
              re.compile(r"^review/eye_"), "review/speaker_check.json", "audio/lines/lines.json", "placed.json",
              "moves.json", "heads.json", "manifest.json", "youtube.json", "learnings.jsonl", "timing.jsonl",
              "drive.jsonl", re.compile(r"^drive_run\d+\.log$")]


# --- small formats ---


def unit_home(stage: str, unit: str) -> str:
    """The unit's folder under the book (db._order_defaults' grammar)."""
    return f"episodes/{unit}" if stage == "episode" else stage


def kind_of(rel: str) -> str | None:
    """image / video / audio / doc / text / log, or None for a file the Viewer does not draw."""
    return KINDS.get(PurePosixPath(rel).suffix.lower())


def clock(ts: float, tz: tzinfo | None = None) -> str:
    return datetime.fromtimestamp(ts, tz).strftime("%H:%M")


def day_clock(ts: float, tz: tzinfo | None = None) -> str:
    d = datetime.fromtimestamp(ts, tz)
    return f"{d.day} {d:%b %H:%M}"


def size(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    return f"{n / 1024:.{1 if n < 10240 else 0}f} KB" if n < 1048576 else f"{n / 1048576:.1f} MB"


def nn(i: int) -> str:
    return f"{i:02d}"


def tk(k: int) -> str:
    return f"T{k:02d}"


def mmss(t: float) -> str:
    return f"{int(t // 60)}:{t % 60:05.2f}"


# --- reads ---


def file_row(path: Path, rel: str) -> dict:
    """One viewable file: unit-relative rel, size, mtime, kind, and whether the doc renderer reads it."""
    st = path.stat()
    kind = kind_of(rel)
    return {"rel": rel, "size": st.st_size, "mtime": st.st_mtime, "kind": kind,
            "doc": kind in ("doc", "text", "log") and st.st_size <= DOC_CAP}


def index_files(folder: Path, cap: int = FILE_CAP) -> list[dict]:
    """Every viewable file under the folder (no __pycache__, no scripts), sorted, at most cap."""
    out = []
    for here, dirs, names in os.walk(folder):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for name in sorted(names):
            rel = (Path(here) / name).relative_to(folder).as_posix()
            if kind_of(rel) and len(out) < cap:
                out.append(file_row(Path(here) / name, rel))
    return sorted(out, key=lambda f: f["rel"])


def read_doc(folder: Path, F: dict, rel: str):
    """A listed JSON file under the cap, parsed; None when missing, too big or broken."""
    f = F.get(rel)
    if not f or f["size"] > DOC_CAP:
        return None
    try:
        return json.loads((folder / rel).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def eye_time(e: dict) -> str:
    return str(e.get("signed_at") or e.get("reviewed_at") or "")


def load_eyes(folder: Path, F: dict) -> dict:
    """The judges' files by kind (panel / take / master), newest signature first, each with its `_rel`."""
    out = {"panel": [], "take": [], "master": []}
    for rel in sorted(r for r in F if EYE.match(r)):
        doc = read_doc(folder, F, rel)
        if isinstance(doc, dict):
            out[EYE_GROUP[rel.split("/")[0]]].append({**doc, "_rel": rel})
    for group in out.values():
        group.sort(key=eye_time, reverse=True)
    return out


def load(folder: Path, unit: str) -> dict:
    """The unit as the joins see it: files by rel, the known docs, the eyes."""
    files = index_files(folder)
    F = {f["rel"]: f for f in files}
    docs = {k: read_doc(folder, F, rel) for k, rel in DOCS.items()}
    return {"unit": unit, "files": files, "F": F, **docs, "eyes": load_eyes(folder, F)}


def run_logs(logs: Path, codex: str, stage: str, run_ids: list) -> list[dict]:
    """The unit's run logs that exist under logs/<codex>/<stage>/, newest run first."""
    out = []
    for run in sorted({r for r in run_ids if r}, reverse=True):
        path = Path(logs) / codex / stage / f"{run}.log"
        if re.fullmatch(r"[\w-]+", run) and path.is_file():
            out.append({"rel": f"_logs/{path.name}", "name": path.name, "run": run,
                        "size": path.stat().st_size, "mtime": path.stat().st_mtime})
    return out


# --- joins (one key each, V03 §2) ---


def _list(U: dict, key: str) -> list:
    v = U.get(key)
    return v if isinstance(v, list) else []


def plan_shots(U: dict) -> list:
    plan = U.get("plan")
    return plan.get("shots") or [] if isinstance(plan, dict) else []


def plan_shot(U: dict, i: int) -> dict | None:
    return next((s for s in plan_shots(U) if s.get("index") == i), None)


def card_of_shot(U: dict, i: int) -> dict | None:
    return next((c for c in _list(U, "cards") if i in (c.get("shots") or [])), None)


def ran_by_index(U: dict, k: int) -> dict:
    return next((c for c in _list(U, "ran") if c.get("index") == k), {})


def still_of(U: dict, i: int) -> dict | None:
    stills = U.get("stills")
    return stills.get(str(i)) if isinstance(stills, dict) else None


def seg_of(U: dict, i: int) -> dict | None:
    qc = U.get("qc") if isinstance(U.get("qc"), dict) else {}
    segs = (qc.get("edit") or {}).get("segments") or []
    return next((s for s in segs if i in (s.get("shots") or [])), None)


def grid_name(unit: str, row: dict) -> str:
    """grids.py's name rule: <unit>_grid_<setup>_<cols>x<rows>[_<tag>]."""
    tag = f"_{row['tag']}" if row.get("tag") else ""
    return f"{unit}_grid_{row.get('setup')}_{row.get('cols')}x{row.get('rows')}{tag}"


def grid_of_shot(U: dict, i: int) -> dict | None:
    """The layout row that draws shot i: grid name, slot, png rel."""
    row = next((r for r in _list(U, "layout") if i in (r.get("shots") or [])), None)
    if row is None:
        return None
    name = grid_name(U["unit"], row)
    return {"name": name, "slot": row["shots"].index(i), "rel": f"storyboard/grids/{name}.png"}


def master_rel(U: dict) -> str | None:
    """The newest master_iterN whose bytes equal master_r2v (the judged one), else master_r2v."""
    r2v = U["F"].get("cut/master_r2v.mp4")
    if r2v is None:
        return None
    iters = [f for f in U["files"] if re.fullmatch(r"cut/master_iter\d+\.mp4", f["rel"]) and f["size"] == r2v["size"]]
    return max(iters, key=lambda f: f["mtime"])["rel"] if iters else r2v["rel"]


def fails_of(U: dict, take: str) -> list[int]:
    """The retired attempt numbers of one take, newest first."""
    pat = re.compile(rf"takes/r2v/attempts/{take}_fail(\d+)\.mp4")
    return sorted((int(m.group(1)) for f in U["files"] if (m := pat.fullmatch(f["rel"]))), reverse=True)


def shot_faults(U: dict, i: int) -> dict:
    """Faults the plan judge and the newest panel eye name on shot i."""
    where = f"shot_{nn(i)}"
    pv = U.get("pv") if isinstance(U.get("pv"), dict) else {}
    panel = U["eyes"]["panel"][0] if U["eyes"]["panel"] else {}
    pick = lambda doc: [f for f in doc.get("faults") or [] if isinstance(f, dict) and f.get("where") == where]  # noqa: E731
    return {"plan": pick(pv), "panel": pick(panel)}


def has(U: dict, rel: str) -> bool:
    return rel in U["F"]


# --- Shots: panel -> staged -> take -> master segment ---


def shot_chips(faults: dict, still) -> list[dict]:
    chips = []
    if faults["panel"]:
        chips.append({"t": f"⚑ panel {len(faults['panel'])}", "cls": "flag"})
    if faults["plan"]:
        chips.append({"t": f"⚑ plan {faults['plan'][0].get('kind')}", "cls": "flag"})
    if still:
        chips.append({"t": "held as a still", "cls": "warn"})
    return chips


def take_layer(U: dict, card: dict | None, i: int, poster: str) -> dict:
    """The shot's take, or why there is none yet."""
    name = tk(card["index"]) if card else tk(i)
    rel, ran = f"takes/r2v/{name}.mp4", ran_by_index(U, card["index"]) if card else {}
    tries = len(fails_of(U, name)) + 1
    missing = None if card and has(U, rel) else (f"not rendered yet: card {name} waits for the shoot" if card else "no take card")
    sub = f"{ran['measured_seconds']} s · try {tries} of {tries}" if ran.get("measured_seconds") else ""
    return {"name": "take", "rel": rel, "poster_rel": poster, "sub": sub, "missing": missing}


def master_layer(U: dict, i: int, poster: str) -> dict:
    """The shot's span in the judged master, in seconds (qc_r2v segments / 24 fps)."""
    seg, mrel, still = seg_of(U, i), master_rel(U), still_of(U, i)
    if not (seg and mrel):
        return {"name": "master", "rel": mrel or "cut/master_r2v.mp4", "missing": "no master yet (assemble)"}
    t0, t1 = seg["start"] / FPS, (seg["start"] + seg["n"]) / FPS
    sub = f"{mmss(t0)}–{mmss(t1)}" + (" · the panel is held, not the take" if still else "")
    return {"name": "master", "rel": mrel, "poster_rel": poster, "seg": {"rel": mrel, "t0": t0, "t1": t1}, "sub": sub}


def panel_layers(U: dict, i: int, p: dict) -> list[dict]:
    n = nn(i)
    return [{"name": "panel", "rel": f"storyboard/shot_{n}.png", "alt": p.get("frame") or "",
             "missing": None if has(U, f"storyboard/shot_{n}.png") else "not drawn yet (panels)"},
            {"name": "staged", "rel": f"storyboard/h3/shot_{n}.png", "alt": f"staged copy for H3: {p.get('frame') or ''}",
             "missing": None if has(U, f"storyboard/h3/shot_{n}.png") else "not staged yet"}]


def shot_item(U: dict, p: dict, k: int) -> dict:
    """One plan shot with its four stages (↑ ↓ walks them)."""
    i = p.get("index", k)
    card = card_of_shot(U, i)
    frame = f"takes/work/content/{tk(card['index'])}_1.png" if card else ""
    poster = frame if has(U, frame) else f"storyboard/shot_{nn(i)}.png"
    faults = shot_faults(U, i)
    return {"id": f"storyboard/shot_{nn(i)}.png", "label": f"Shot {nn(i)}", "short": nn(i), "shot": i,
            "axis": "stage", "sub": f"{str(p.get('size') or '').replace('_', ' ')} · {p.get('setup') or ''}",
            "chips": shot_chips(faults, still_of(U, i)), "flag": bool(faults["panel"] or faults["plan"]),
            "layers": panel_layers(U, i, p) + [take_layer(U, card, i, poster), master_layer(U, i, poster)]}


def shot_items(U: dict) -> list[dict]:
    return [shot_item(U, p, k) for k, p in enumerate(plan_shots(U)) if isinstance(p, dict)]


# --- Takes: kept -> failed attempts -> head trim ---


def take_chips(U: dict, name: str, still) -> tuple[list[dict], bool]:
    eye = U["eyes"]["take"][0] if U["eyes"]["take"] else None
    mine = [f for f in (eye or {}).get("faults") or [] if isinstance(f, dict) and f.get("where") == name]
    chips = [{"t": f"⚑ {', '.join(str(f.get('kind')) for f in mine)}", "cls": "flag"}] if mine else \
        ([{"t": "EYE_TAKES ✓", "cls": "ok"}] if eye else [])
    if still:
        chips.append({"t": "not in the master: still", "cls": "warn"})
    return chips, bool(mine)


def take_layers(U: dict, name: str, ran: dict, poster: str | None) -> list[dict]:
    fails = fails_of(U, name)
    tries, secs = len(fails) + 1, ran.get("measured_seconds")
    layers = [{"name": "kept", "rel": f"takes/r2v/{name}.mp4", "poster_rel": poster,
               "sub": f"try {tries} of {tries}" + (f" · {secs} s" if secs else "")}]
    layers += [{"name": f"fail{k}", "rel": f"takes/r2v/attempts/{name}_fail{k}.mp4",
                "sub": f"try {k} of {tries} · retired · recipe not recorded"} for k in fails]
    if has(U, f"takes/work/dq/{name}_head.mp4"):
        layers.append({"name": "head", "rel": f"takes/work/dq/{name}_head.mp4", "sub": "head trim (take_dq)"})
    return layers


def take_item(U: dict, card: dict) -> dict:
    name, ran = tk(card["index"]), ran_by_index(U, card["index"])
    frame = f"takes/work/content/{name}_1.png"
    poster = frame if has(U, frame) else None
    chips, flag = take_chips(U, name, still_of(U, card["index"]))
    layers, secs = take_layers(U, name, ran, poster), ran.get("measured_seconds")
    return {"id": f"takes/r2v/{name}.mp4", "label": name, "short": name, "shots": card.get("shots") or [],
            "shot": (card.get("shots") or [card["index"]])[0], "axis": "attempt",
            "sub": f"shots {' '.join(nn(s) for s in card.get('shots') or [])} · {card.get('setup') or ''}",
            "chips": chips, "flag": flag, "badge": f"+{len(layers) - 1}" if len(layers) > 1 else "",
            "dur": f"{secs}s" if secs else "", "layers": layers, "strip_rel": poster}


def take_items(U: dict) -> list[dict]:
    cards = [c for c in _list(U, "cards") if isinstance(c, dict) and "index" in c]
    return [take_item(U, c) for c in cards if has(U, f"takes/r2v/{tk(c['index'])}.mp4")]


def fail_count(U: dict) -> str:
    n = sum(1 for f in U["files"] if re.fullmatch(r"takes/r2v/attempts/T\d+_fail\d+\.mp4", f["rel"]))
    return f"+{n}" if n else ""


# --- Grids: current draw -> superseded draws ---


def grid_rels(U: dict) -> list[str]:
    """The live grids in layout order, then any grid the layout does not name."""
    live = [f["rel"] for f in U["files"] if re.fullmatch(r"storyboard/grids/[^/]+\.png", f["rel"])]
    order = [f"storyboard/grids/{grid_name(U['unit'], r)}.png" for r in _list(U, "layout") if isinstance(r, dict)]
    return [r for r in order if r in live] + sorted(r for r in live if r not in order)


def grid_revisions(U: dict, name: str) -> list[dict]:
    """Earlier draws of this grid: same file name in a superseded or reason folder, newest first."""
    pat = re.compile(rf"storyboard/(superseded/[^/]+|grids/[^/]+)/{re.escape(name)}\.png")
    old = sorted((f for f in U["files"] if pat.fullmatch(f["rel"])), key=lambda f: f["mtime"], reverse=True)
    return [{"name": f["rel"].split("/")[-2], "rel": f["rel"], "sub": f"superseded · {day_clock(f['mtime'])}"}
            for f in old]


def grid_item(U: dict, rel: str) -> dict:
    name = PurePosixPath(rel).stem
    m = re.search(r"_grid_(.+?)_(\d+)x(\d+)(?:_(.+))?$", name)
    setup, cols, rows, tag = m.groups() if m else (name, "?", "?", None)
    row = next((r for r in _list(U, "layout") if isinstance(r, dict) and grid_name(U["unit"], r) == name), None)
    f, revs = U["F"][rel], grid_revisions(U, name)
    shots = row["shots"] if row else []
    return {"id": rel, "label": f"{setup.replace('_', ' ')} {cols}×{rows}{' ' + tag if tag else ''}",
            "short": f"{setup.split('_')[0]} {cols}×{rows}", "axis": "revision", "shots": shots,
            "shot": shots[0] if shots else None,
            "sub": (f"shots {' '.join(nn(s) for s in shots)}" if row else "not in layout.json") + f" · {clock(f['mtime'])}",
            "chips": [] if row else [{"t": "not in layout.json", "cls": "warn"}], "badge": f"+{len(revs)}" if revs else "",
            "layers": [{"name": "current", "rel": rel, "sub": f"drawn {day_clock(f['mtime'])}"}] + revs}


def grid_items(U: dict) -> list[dict]:
    return [grid_item(U, rel) for rel in grid_rels(U)]


# --- Masters: iterations folded by equal bytes ---


def master_groups(U: dict) -> list[dict]:
    """master_iterN newest first, an iteration equal in bytes to a newer one folded into it."""
    iters = sorted((f for f in U["files"] if re.fullmatch(r"cut/master_iter\d+\.mp4", f["rel"])),
                   key=lambda f: int(re.search(r"iter(\d+)", f["rel"]).group(1)), reverse=True)
    seen: dict[int, dict] = {}
    for f in iters:
        if f["size"] in seen:
            seen[f["size"]]["also"].append(re.search(r"iter\d+", f["rel"]).group(0))
        else:
            seen[f["size"]] = {"f": f, "also": []}
    r2v = U["F"].get("cut/master_r2v.mp4")
    if r2v and r2v["size"] in seen:
        seen[r2v["size"]]["also"].append("master_r2v")
    return list(seen.values())


def master_poster(U: dict) -> str | None:
    qc = U.get("qc") if isinstance(U.get("qc"), dict) else {}
    for rel in (f"review/contact_{qc.get('sha8')}.png", "storyboard/contact.png"):
        if has(U, rel):
            return rel
    return None


def master_item(U: dict, g: dict, poster: str | None) -> dict:
    f, also = g["f"], g["also"]
    n = re.search(r"iter(\d+)", f["rel"]).group(1)
    judged = "master_r2v" in also
    qc = U.get("qc") if isinstance(U.get("qc"), dict) else {}
    faults = len((U["eyes"]["master"][0] if U["eyes"]["master"] else {}).get("faults") or [])
    chips = [{"t": f"MASTER ⚑ {faults} · {qc.get('sha8', '')}", "cls": "flag" if faults else "ok"}] if judged \
        else [{"t": "no verdict kept", "cls": ""}]
    sub = f"{mmss(qc['seconds'])} · LUFS {qc.get('lufs')}" if judged and qc.get("seconds") else "no QC kept for this iteration"
    return {"id": f["rel"], "label": f"v{n}", "short": f"v{n}", "judged": judged, "chips": chips, "strip_rel": poster,
            "sub": f"iter{n}{' = ' + ' = '.join(also) if also else ''} · {size(f['size'])} · {day_clock(f['mtime'])}",
            "layers": [{"name": "master", "rel": f["rel"], "poster_rel": poster, "sub": sub}]}


def master_items(U: dict) -> list[dict]:
    poster = master_poster(U)
    return [master_item(U, g, poster) for g in master_groups(U)]


# --- Files: the known docs, then the logs ---


def ordered_docs(U: dict) -> list[dict]:
    docs, out = [f for f in U["files"] if f["doc"]], []
    for p in FILE_ORDER:
        out += [f for f in docs if (f["rel"] == p if isinstance(p, str) else p.match(f["rel"])) and f not in out]
    return out


def file_items(U: dict, logs: list[dict]) -> list[dict]:
    """The Files sequence: the unit's known docs in reading order, then its run logs."""
    items = [{"id": f["rel"], "label": f["rel"].split("/")[-1], "short": f["rel"].split("/")[-1],
              "sub": f"{f['rel']} · {size(f['size'])} · {day_clock(f['mtime'])}",
              "layers": [{"rel": f["rel"], "kind": f["kind"]}]} for f in ordered_docs(U)]
    items += [{"id": x["rel"], "label": f"run log {x['run'].split('__')[-1]}", "short": x["run"].split("__")[-1],
               "sub": f"logs/…/{x['name']} · {size(x['size'])}", "run": x["run"],
               "layers": [{"rel": x["rel"], "kind": "log", "title": x["name"]}]} for x in logs]
    return items


def sequences(U: dict, logs: list[dict]) -> list[dict]:
    """The five tabs, in key order 1-5."""
    return [{"id": "shots", "name": "Shots", "items": shot_items(U)},
            {"id": "takes", "name": "Takes", "items": take_items(U), "extra": fail_count(U)},
            {"id": "grids", "name": "Grids", "items": grid_items(U)},
            {"id": "masters", "name": "Masters", "items": master_items(U)},
            {"id": "files", "name": "Files", "items": file_items(U, logs)}]


def unit_model(folder: Path, codex: str, stage: str, unit: str, home: str, logs: list[dict]) -> dict:
    """What GET /viewer/<codex>/<stage>/<unit>.json answers."""
    U = load(folder, unit)
    return {"codex": codex, "stage": stage, "unit": unit, "home": home, "files": U["files"], "logs": logs,
            "seqs": sequences(U, logs)}
