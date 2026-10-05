"""The live card's data (progress tracker spec §3): `progress()` is the one
function of the card that touches disk.  It folds the run's progress events
(v1: derived by `legacy_progress` from what the run already writes), asks the
process table whether the drive is alive, measures the step norms, and returns
the `models.Progress` shape -- the rail, the running step, the contact sheet's
items, the finish band, the vital and its signal trace.

History is cached for a minute and JSON files by mtime, so a 2 s poll stays
well under 30 ms; the finish is recomputed at most once a minute."""
from __future__ import annotations

import re
import sqlite3
import time
from datetime import datetime
from pathlib import Path

from studio import eta, progress as prog
from studio.command_center import legacy_progress as lp
from studio.command_center import library_paths, procs, unit_view, vitals
from studio.run_budget import EPISODE_CEILING_SECONDS

STAGE = "episode"
COUNTED = ("07", "08", "09")
CHECKS = ("take_dq", "take_content", "strip", "take_eye")
RUNNING = ("live", "quiet", "stalled")
HISTORY_TTL, ETA_TTL = 60.0, 60.0
_cache: dict = {}


# --- small reads ---


def number_of(unit: str) -> int | None:
    """17 from `ep17`."""
    m = re.search(r"(\d+)$", unit or "")
    return int(m.group(1)) if m else None


def version(path: Path) -> str:
    """`?v=<mtime_ns base 36>`: a new picture is a new URL."""
    n, digits, out = Path(path).stat().st_mtime_ns, "0123456789abcdefghijklmnopqrstuvwxyz", ""
    while n:
        n, r = divmod(n, 36)
        out = digits[r] + out
    return f"?v={out or '0'}"


def timing_files(book: Path) -> list[list[dict]]:
    """Every episode's timing.jsonl rows in the book, each parsed once per mtime."""
    out = []
    for path in sorted(Path(book).glob("episodes/*/timing.jsonl")):
        key = ("timing", str(path), path.stat().st_mtime_ns)
        if key not in _cache:
            _cache[key] = lp.jsonl_rows(lp.read_tail(path))
        out.append(_cache[key])
    return out


def history(conn: sqlite3.Connection, book: Path, now: float) -> dict[str, list[float]]:
    """{step: [secs]}: the events table's same-run pairs, with timing.jsonl's
    per-episode sums for a step that has fewer than three; cached a minute."""
    hit = _cache.get(("history", str(book)))
    if hit and now - hit[0] < HISTORY_TTL:
        return hit[1]
    measured = eta.step_history(conn, STAGE)
    for step, xs in eta.timing_history(timing_files(book)).items():
        if len(measured.get(step, [])) < 3:
            measured[step] = xs
    _cache[("history", str(book))] = (now, measured)
    return measured


def runner_rows(logs: Path, codex: str, run_id: str | None) -> list[dict]:
    """The run's own log rows (logs/<codex>/episode/<run_id>.log)."""
    return lp.jsonl_rows(lp.read_tail(Path(logs) / codex / STAGE / f"{run_id}.log")) if run_id else []


def work_before(home: Path, t0: float | None) -> float:
    """Seconds this episode's earlier runs logged in timing.jsonl (local stamps, before t0)."""
    rows = lp.jsonl_rows(lp.read_tail(home / "timing.jsonl"))
    return sum(float(r.get("seconds") or 0) for r in rows
               if t0 is None or (eta.to_epoch(r.get("started")) or 0) < t0)


# --- the rail ---


def _pair(db_rows: list[dict], run_id: str | None, sid: str) -> tuple[float | None, float | None]:
    """(started, ended) of one step inside this run."""
    began = ended = None
    for r in db_rows:
        if r.get("run_id") == run_id and str(r.get("step_id")) == sid:
            if r.get("event") == "started":
                began = eta.to_epoch(r.get("event_ts"))
            elif r.get("event") in ("completed", "failed", "deferred", "escalated"):
                ended = eta.to_epoch(r.get("event_ts"))
    return began, ended


def retries(db_rows: list[dict], run_id: str | None, sid: str) -> int:
    """How many earlier runs of this unit started the step."""
    return len({r.get("run_id") for r in db_rows if str(r.get("step_id")) == sid
                and r.get("event") == "started" and r.get("run_id") != run_id})


RAIL_STATE = {"start": "running", "done": "done", "skip": "skip", "fail": "fail",
              "deferred": "deferred", "refused": "refused", "escalated": "escalated"}


def rail(state: dict, db_rows: list[dict], hist: dict, names: dict[str, str], now: float) -> list[dict]:
    """Every step of the stage: its state in this run, its seconds, its norm."""
    out = []
    for sid, name in names.items():
        began, ended = _pair(db_rows, state["run"], sid)
        st = RAIL_STATE.get((state["steps"].get(sid) or {}).get("state"), "waiting")
        secs = (ended - began) if began and ended else (now - began if began and st == "running" else None)
        xs = hist.get(sid) or []
        out.append({"id": sid, "name": name, "state": st, "secs": secs,
                    "median_s": eta.band(xs)[1] if xs else None, "retries": retries(db_rows, state["run"], sid)})
    return out


# --- the contact sheet ---


def media(home: Path, sid: str, item: str) -> tuple[str | None, str | None]:
    """(panel, video) under the episode folder, versioned; None when not on disk."""
    shot = item[1:] if item.startswith("T") else item
    panel = next((p for p in (home / "storyboard" / "h3" / f"shot_{shot}.png",
                              home / "storyboard" / f"shot_{shot}.png") if p.is_file()), None)
    take = home / "takes" / "r2v" / f"{item}.mp4"
    rel_panel = panel.relative_to(home).as_posix() + version(panel) if panel else None
    video = f"takes/r2v/{item}.mp4" + version(take) if sid == "09" and take.is_file() else None
    return rel_panel, video


def items(state: dict, home: Path, sid: str | None, running: bool, pace: float) -> list[dict]:
    """One tile per planned item; the first waiting one renders while the run is alive."""
    out, rendering = [], running
    for item, weight in state["plan"]:
        st = prog.item_state(state, item)
        if st == "waiting" and rendering:
            st, rendering = "rendering", False
        panel, video = media(home, sid or "", item)
        secs = (state["done"].get(item) or [None])[-1]
        prior = eta.take_prior(int(weight)) * pace if sid == "09" and st == "rendering" else None
        out.append({"id": item, "state": st, "panel": panel, "video": video if st != "waiting" else None,
                    "secs": secs, "prior_s": prior})
    return out


def inflight_started(state: dict) -> float | None:
    """When the take now rendering began: the latest landing, else the plan."""
    times = [state["landed"][i] for i in state["fresh"] if i in state["landed"]]
    return max(times + [state["plan_t"] or 0.0]) or None


# --- the running step ---


def counted(state: dict) -> bool:
    return state["step"] in COUNTED and bool(state["plan"])


def current(state: dict, tiles: list[dict]) -> str | None:
    """What the step is on: the take or panel rendering, else the checks, else the last rung."""
    if counted(state):
        hot = next((t["id"] for t in tiles if t["state"] == "rendering"), None)
        noun = "take" if state["step"] == "09" else "panel"
        return f"{noun} {hot}" if hot else ("checking takes" if state["step"] == "09" else None)
    rung = (state["rounds"] or [None])[-1]
    return f"{rung['gate']} round {len(state['rounds'])} · {rung['action']}" if rung else None


def now_step(state: dict, names: dict[str, str], tiles: list[dict]) -> dict | None:
    """The hero's subject: the running step, counted or loop, with its ladder rungs."""
    sid = state["step"]
    if sid is None:
        return None
    done, total, wd, wt = prog.counts(state) if counted(state) else (0, 0, 0.0, 0.0)
    rungs = [{k: r[k] for k in ("gate", "measured", "action", "terminal")} for r in state["rounds"][-8:]]
    return {"id": sid, "name": names.get(sid, ""), "kind": "counted" if counted(state) else "loop",
            "done": done, "total": total, "weight_done": wd, "weight_total": wt,
            "current": current(state, tiles), "sampler": None, "rounds": rungs}


# --- the finish ---


def take_left(state: dict, frames: dict[str, int], now: float) -> dict:
    """The takes still to land, the one in flight first, through eta.take_remaining."""
    done = [((state["done"][i] or [None])[-1], frames.get(i, 0)) for i in state["fresh"]]
    done = [(s, f) for s, f in done if s]
    left = [frames.get(i, int(w)) for i, w in state["plan"] if prog.item_state(state, i) in ("waiting", "failed")]
    started = inflight_started(state)
    return eta.take_remaining(done, left, cold_paid=bool(state["done"]),
                              inflight_s=(now - started) if started and left else None)


def step_left(state: dict, hist: dict, book: Path, frames: dict[str, int], now: float) -> dict:
    """{left, sigma, basis, n} for the running step; left is None past p90."""
    sid, xs = state["step"], hist.get(state["step"] or "", [])
    if sid == "09" and counted(state):
        t = take_left(state, frames, now)
        return {"left": t["secs"] + eta.sub_norm(timing_files(book), CHECKS), "sigma": t["spread"],
                "basis": t["basis"], "n": len(xs), "r": t["r"]}
    elapsed = now - (state["step_t"] or now)
    return {"left": eta.remaining_unknown(elapsed, xs), "sigma": eta.sigma(xs),
            "basis": eta.confidence(xs), "n": len(xs), "r": eta.SEED}


def clock(epoch: float | None) -> str:
    """`02:45` in this machine's local time."""
    return datetime.fromtimestamp(epoch).strftime("%H:%M") if epoch else ""


def finish(state: dict, hist: dict, names: dict, left: dict, now: float, work_s: float) -> dict:
    """The rounded finish band, held for a minute per run and step."""
    key = ("eta", state["run"], state["step"])
    hit = _cache.get(key)
    if hit and now - hit[0] < ETA_TTL:
        return hit[1]
    later = [hist.get(s) or [0.0] for s in names if s > (state["step"] or "")]
    e = eta.episode_eta(now, left["left"], left["sigma"], later, now + EPISODE_CEILING_SECONDS - work_s)
    out = {**{k: (eta.round_to(e[k]) if e[k] else None) for k in ("finish_at", "lo", "hi")},
           "basis": left["basis"], "n_runs": left["n"], "long": e["long"], "capped": e["capped"]}
    out.update(finish=clock(out["finish_at"]), range=f"{clock(out['lo'])}–{clock(out['hi'])}" if out["lo"] else "")
    _cache[key] = (now, out)
    return out


# --- the card ---


def master(library: Path, codex: str, home: Path) -> tuple[str | None, dict | None]:
    """The delivered master's URL and its QC summary, for the hand-over."""
    rel = library_paths.book_relative(home / "cut" / "master_r2v.mp4", codex)
    url = library_paths.artefact_url(codex, rel) if rel and (home / "cut" / "master_r2v.mp4").is_file() else None
    qc = lp.cached_json(home / "qc_r2v.json")
    keep = ("seconds", "lufs", "lufs_ok", "true_peak", "tp_ok")
    return url, {k: qc.get(k) for k in keep} if isinstance(qc, dict) else None


def title(vital: str, step: dict | None, finish_at: str, unit: str) -> str:
    """`● 09 shoot 11/26 · ~02:45 · ep17` -- the tab's name."""
    mark = {"live": "●", "quiet": "○", "stalled": "◐", "done": "✓"}.get(vital, "✕")
    if step is None:
        return f"{mark} {unit}"
    count = f" {step['done']}/{step['total']}" if step["kind"] == "counted" else ""
    when = f" · ~{finish_at}" if finish_at and vital in RUNNING else ""
    return f"{mark} {step['id']} {step['name']}{count}{when} · {unit}"


def _vital(state: dict, derived: dict, frames: dict, hist: dict, alive: bool, now: float) -> dict:
    """The vital with its silence and budget."""
    quiet = vitals.quiet_seconds(derived["signals"], now)
    hot = next((frames.get(i, int(w)) for i, w in state["plan"] if prog.item_state(state, i) == "waiting"), 0)
    budget = vitals.step_budget(state["step"], hot if counted(state) else 0, not state["done"], hist)
    v = vitals.vital(state, alive, quiet, budget, derived["refusal"] if state["outcome"] else "")
    if state["run"] is None:
        v = {"vital": "idle", "reason": "no run yet"}
    return {**v, "quiet_s": quiet, "budget_s": budget}


def progress(library: Path, conn: sqlite3.Connection, codex: str, unit: str, now: float | None = None,
             logs: Path | None = None, proc_rows: list | None = None, comfy=None) -> dict | None:
    """The live card for one episode unit; None when the book or the unit has no folder."""
    now, book = now or time.time(), library_paths.book_folder(library, codex)
    home = book / "episodes" / unit if book else None
    if home is None or not home.is_dir():
        return None
    db_rows = unit_view.unit_events(conn, codex, STAGE, unit)
    log, _ = lp.newest_log(home)
    run_id = lp.banner_run(lp.read_tail(log)) if log else None
    derived = lp.derive(home, db_rows, runner_rows(Path(logs or Path(library).parent / "logs"), codex, run_id))
    return assemble(library, codex, unit, home, conn, db_rows, derived, now, proc_rows, comfy)


def assemble(library, codex, unit, home, conn, db_rows, derived, now, proc_rows, comfy) -> dict:
    """The card from the derived events: fold, liveness, rail, sheet, finish."""
    state = prog.fold(derived["events"])
    names = lp.registry_names() or {k: v["name"] for k, v in state["steps"].items()}
    hist, frames = history(conn, home.parent.parent, now), lp.take_frames(home)
    rows = procs.list_processes() if proc_rows is None else proc_rows
    alive = vitals.pid_alive(procs.find_drive(rows, codex, number_of(unit) or -1), state["t0"])
    v = _vital(state, derived, frames, hist, alive, now)
    left = step_left(state, hist, home.parent.parent, frames, now)
    tiles = items(state, home, state["step"], v["vital"] in RUNNING, left["r"])
    elapsed = now - state["t0"] if state["t0"] else 0.0
    work = work_before(home, state["t0"]) + elapsed
    e = finish(state, hist, names, left, now, work) if v["vital"] in RUNNING else {}
    return card(library, codex, unit, home, state, db_rows, hist, names, derived, v, tiles, e, now, work)


def card(library, codex, unit, home, state, db_rows, hist, names, derived, v, tiles, e, now, work) -> dict:
    """The `models.Progress` dict."""
    step = now_step(state, names, tiles)
    url, qc = master(library, codex, home) if v["vital"] == "done" else (None, None)
    return {"codex": codex, "unit": unit, "run_id": state["run"], "vital": v["vital"], "vital_reason": v["reason"],
            "quiet_s": v["quiet_s"], "budget_s": v["budget_s"], "run_started": state["t0"],
            "step_started": state["step_t"], "now": now, "elapsed_s": now - state["t0"] if state["t0"] else 0.0,
            "work_s": work, "ceiling_s": float(EPISODE_CEILING_SECONDS),
            "steps": rail(state, db_rows, hist, names, now), "now_step": step, "items": tiles,
            "inflight_started": inflight_started(state) if counted(state) else None,
            "media_base": f"/thumb/{codex}/160/episodes/{unit}/", "lib_base": f"/lib/{codex}/episodes/{unit}/",
            "eta": e, "trace": [round(t, 1) for t in vitals.trace(derived["signals"], now)],
            "last_words": derived["refusal"] if v["vital"] == "refused" else derived["last_words"],
            "title": title(v["vital"], step, e.get("finish", ""), unit), "master": url, "qc": qc}
