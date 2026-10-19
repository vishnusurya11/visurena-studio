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
from datetime import datetime, timedelta, timezone
from pathlib import Path

from studio import eta, progress as prog, registry
from studio.command_center import legacy_progress as lp
from studio.command_center import loops, workgrid
from studio.command_center import library_paths, procs, unit_view, vitals
from studio.run_budget import EPISODE_CEILING_SECONDS, OWNER_LIMIT_SECONDS

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
    per-episode sums for a step that has fewer than three, trimmed to full runs
    (eta.full_runs: a resume that kept the work is not a norm); cached a minute."""
    hit = _cache.get(("history", str(book)))
    if hit and now - hit[0] < HISTORY_TTL:
        return hit[1]
    measured = eta.step_history(conn, STAGE)
    for step, xs in eta.timing_history(timing_files(book)).items():
        if len(measured.get(step, [])) < 3:
            measured[step] = xs
    measured = {step: eta.full_runs(xs) for step, xs in measured.items()}
    _cache[("history", str(book))] = (now, measured)
    return measured


def runner_rows(logs: Path, codex: str, run_id: str | None) -> list[dict]:
    """The run's own log rows (logs/<codex>/episode/<run_id>.log)."""
    return lp.jsonl_rows(lp.read_tail(Path(logs) / codex / STAGE / f"{run_id}.log")) if run_id else []


def work_before(home: Path, t0: float | None) -> float:
    """Seconds this episode spent before t0 on the honest clock (studio.run_clock,
    C3_verdict #3): the union of its run spans, a killed run to its last beat,
    plus legacy timing.jsonl rows from before the first run row."""
    from studio import run_clock
    return run_clock.spent_before(home, t0)


# --- the rail ---


def _pair(db_rows: list[dict], run_id: str | None, sid: str) -> tuple[float | None, float | None]:
    """(started, ended) of one step inside this run."""
    began = ended = None
    for r in db_rows:
        if r.get("run_id") == run_id and str(r.get("step_id")) == sid:
            if r.get("event") == "started":
                began = eta.to_epoch(r.get("event_ts"))
            elif r.get("event") in ("completed", "skipped", "failed", "deferred", "escalated"):
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
        out.append({"id": sid, "name": name, "state": st, "secs": secs, "end": ended,
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


SEATTLE = "America/Los_Angeles"


def _nth_sunday(year: int, month: int, n: int) -> float:
    """00:00 UTC of the month's n-th Sunday, as epoch seconds."""
    d = datetime(year, month, 1, tzinfo=timezone.utc)
    return (d + timedelta(days=(6 - d.weekday()) % 7 + 7 * (n - 1))).timestamp()


def pacific_offset(epoch: float) -> int:
    """-7 inside US daylight time (2nd Sunday of March 02:00 PST to 1st Sunday of
    November 02:00 PDT), else -8: Seattle with no tz database on the box."""
    year = datetime.fromtimestamp(epoch, timezone.utc).year
    spring, fall = _nth_sunday(year, 3, 2) + 10 * 3600, _nth_sunday(year, 11, 1) + 9 * 3600
    return -7 if spring <= epoch < fall else -8


def seattle_time(epoch: float) -> datetime:
    """The moment in Seattle: the tz database when the box has one, else the US rule."""
    try:
        from zoneinfo import ZoneInfo
        return datetime.fromtimestamp(epoch, ZoneInfo(SEATTLE))
    except Exception:                                  # noqa: BLE001 -- no tzdata on Windows
        return datetime.fromtimestamp(epoch, timezone(timedelta(hours=pacific_offset(epoch))))


def clock(epoch: float | None) -> str:
    """`6:45 pm` in Seattle (owner: every time Seattle, 12-hour)."""
    if not epoch:
        return ""
    d = seattle_time(epoch)
    return f"{d.hour % 12 or 12}:{d.minute:02d} {'am' if d.hour < 12 else 'pm'}"


def clock_range(lo: float | None, hi: float | None) -> str:
    """`6:15–7:15 pm`, the half of the day said once when both ends share it."""
    a, b = clock(lo), clock(hi)
    return f"{a[:-3]}–{b}" if a[-2:] == b[-2:] else f"{a}–{b}"


def left_words(secs: float | None) -> str:
    """`3h 05m` / `42m` / `<1m`: the hero's time left; '' with no finish."""
    if secs is None:
        return ""
    m = int(max(0.0, secs) // 60)
    return f"{m // 60}h {m % 60:02d}m" if m >= 60 else (f"{m}m" if m else "<1m")


# --- this make (the runs on the episode's honest clock) ---


STEP_ROW = re.compile(r"step_(\d\d)$")


def make_runs(home: Path, run_id: str | None) -> set[str]:
    """The run ids of this make: clock.jsonl's rows, the open run, and this run."""
    from studio import run_clock
    ids = {r.get("run_id") for r in run_clock.rows(home)} | {(run_clock.read_open(home) or {}).get("run_id")}
    return {i for i in ids | {run_id} if i}


def make_start(home: Path, t0: float | None) -> float | None:
    """When this make began: its first run span, else this run."""
    from studio import run_clock
    starts = [a for a, _ in run_clock.spans(home)] + ([t0] if t0 else [])
    return min(starts) if starts else None


def make_steps(rows: list[dict], since: float | None) -> dict[str, dict]:
    """{step: {secs, end}} from timing.jsonl since the make began: a `step_NN` started
    row opens a span, the work rows after it stretch its end; spans of a step sum."""
    spans: dict[str, list[list[float]]] = {}
    cur = None
    for r in rows:
        t0 = eta.to_epoch(r.get("started"))
        if t0 is None or (since and t0 < since - 5):
            continue
        m = STEP_ROW.match(str(r.get("stage") or ""))
        if m and r.get("event") == "started":
            cur = [t0, t0]
            spans.setdefault(m.group(1), []).append(cur)
        elif cur is not None:
            cur[1] = max(cur[1], eta.to_epoch(r.get("ended")) or t0)
    return {sid: {"secs": sum(b - a for a, b in xs), "end": max(b for _, b in xs)} for sid, xs in spans.items()}


def finished(s: dict) -> bool:
    """Done or skipped in this run, or a later step kept from this make."""
    return s.get("state") in ("done", "skip") or s.get("window") == "kept"


def finished_words(s: dict) -> str:
    """`50m · 3:52 pm`: a finished step's time in this make and its Seattle end."""
    made = s.get("made")
    if not finished(s) or not made:
        return ""
    return f"{unit_view.span(made['secs']) or '<1m'} · {clock(made['end'])}"


def kept_steps(db_rows: list[dict], runs: set[str] | None = None) -> set[str]:
    """Steps a run of THIS make finished (completed or skipped); an earlier make's
    finish is not kept (owner 2026-10-18: 07/08 read `kept` with no grid on disk)."""
    return {str(r.get("step_id")) for r in db_rows if r.get("event") in ("completed", "skipped")
            and (runs is None or r.get("run_id") in runs)}


def later_steps(state: dict, hist: dict, names: dict, db_rows: list[dict], unit: str,
                runs: set[str] | None = None) -> list[tuple]:
    """(step, will run, full-run history) for each step after the running one (eta.will_run
    over the registry's in:/out:); every later step runs when the registry cannot answer."""
    order = list(names)
    try:
        ins = {s: registry.inputs_of(STAGE, s, unit) for s in order}
        outs = {s: registry.outputs_of(STAGE, s, unit) for s in order}
    except (KeyError, OSError, ValueError, TypeError):
        ins, outs = {}, {}
    will = eta.will_run(order, state["step"] or "", kept_steps(db_rows, runs) if ins else set(), ins, outs)
    return [(s, runs, hist.get(s) or []) for s, runs in will.items()]


def rework(conn: sqlite3.Connection, now: float) -> tuple[float, float, int]:
    """The relaunch rework band of the most recent delivered units (eta.rework_band), a minute."""
    hit = _cache.get(("rework",))
    if hit and now - hit[0] < HISTORY_TTL:
        return hit[1]
    units = eta.finished_units(conn, last_n=eta.REWORK_LAST_N)
    band = eta.rework_band(eta.rework_shares(eta.episode_pairs(conn), units))
    _cache[("rework",)] = (now, band)
    return band


def finish(state: dict, left: dict, later: list[tuple], now: float, work_s: float,
           band: tuple[float, float, int] = (eta.REWORK_PRIOR, 2 * eta.REWORK_PRIOR, 0)) -> dict:
    """The episode's rounded finish band with the measured relaunch rework (eta.with_rework),
    the running step's end and each later step's window, held a minute per run, step and round."""
    key = ("eta", state["run"], state["step"], len(state["rounds"]))
    hit = _cache.get(key)
    if hit and now - hit[0] < ETA_TTL:
        return hit[1]
    ceiling = now + EPISODE_CEILING_SECONDS - work_s
    p = eta.with_rework(eta.project(now, left["left"], left["sigma"], later, ceiling), now, band, ceiling)
    out = {**{k: (eta.round_to(p[k]) if p[k] else None) for k in ("finish_at", "lo", "hi")},
           "basis": left["basis"], "n_runs": left["n"], "long": p["long"], "capped": p["capped"],
           "steps_left": p["steps_left"], "plan": p["steps"], "step_end": clock(p["step_end_at"]),
           "finish_raw": p["finish_at"], "rework": p["rework"], "rework_n": p["rework_n"],
           "firm": eta.firmness(p["rework_n"], p["long"], p["hi"] - p["finish_at"])}
    out.update(finish=clock(out["finish_at"]), range=clock_range(out["lo"], out["hi"]) if out["lo"] else "")
    _cache[key] = (now, out)
    return out


def window_words(w: dict) -> str:
    """A later step on the rail: `~18m` projected, `kept` (finished in this make), or `—`."""
    if not w.get("will_run"):
        return "kept"
    if w.get("start_at") is None or w.get("end_at") is None:
        return "—"
    return f"~{left_words(w['end_at'] - w['start_at'])}"


def with_windows(steps: list[dict], plan: dict | None) -> list[dict]:
    """The rail's steps, each later one with its words (window_words) and its
    Seattle `5:01–5:19 pm` for the tooltip."""
    by = {w["id"]: w for w in (plan or {}).get("steps") or []}
    out = []
    for s in steps:
        w = by.get(s["id"])
        if w:
            s = {**s, "will_run": w["will_run"], "window": window_words(w),
                 "when": clock_range(w["start_at"], w["end_at"]) if w["will_run"] and w.get("start_at") else ""}
        out.append(s)
    return out


def with_made(steps: list[dict], made: dict[str, dict]) -> list[dict]:
    """Each finished step with its time in this make and its end: `50m · 3:52 pm`."""
    out = []
    for s in steps:
        m = made.get(s["id"]) or ({"secs": s.get("secs") or 0.0, "end": s["end"]} if s.get("end") else None)
        m = m if finished(s) else None
        s = {**s, "made": m} if m else s
        out.append({**s, "fin": finished_words(s)})
    return out


# --- the card ---


def home_timing(home: Path) -> list[dict]:
    """This episode's timing.jsonl rows, parsed once per mtime."""
    path = Path(home) / "timing.jsonl"
    if not path.is_file():
        return []
    key = ("timing", str(path), path.stat().st_mtime_ns)
    if key not in _cache:
        _cache[key] = lp.jsonl_rows(lp.read_tail(path))
    return _cache[key]


def work_rows(library: Path, codex: str, unit: str) -> list[dict]:
    """The work grid under the live card (workgrid; timeline debate D3): clean shots folded."""
    book = library_paths.book_folder(library, codex)
    home = book / "episodes" / unit if book else None
    return workgrid.fold(workgrid.grid(workgrid.read(home, unit))) if home and home.is_dir() else []


def with_left(e: dict, now: float) -> dict:
    """The hero's time left from the unrounded finish, fresh every poll (`3h 05m`)."""
    raw = e.get("finish_raw")
    return {**e, "left_s": raw - now, "left": left_words(raw - now)} if raw else e


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


def run_alive(pid_alive: bool, beat: float | None, files_alive: bool, now: float) -> bool:
    """The drive process, else the run's own clock beat when it has one (page experts
    2026-10-18: a paused series read 'stalled' on moving files), else the folder's mtimes."""
    if pid_alive:
        return True
    return now - beat < unit_view.BEAT_FRESH_S if beat else files_alive


def assemble(library, codex, unit, home, conn, db_rows, derived, now, proc_rows, comfy) -> dict:
    """The card from the derived events: fold, liveness, rail, sheet, finish."""
    state = prog.fold(derived["events"])
    names = lp.registry_names() or {k: v["name"] for k, v in state["steps"].items()}
    hist, frames = history(conn, home.parent.parent, now), lp.take_frames(home)
    rows = procs.list_processes() if proc_rows is None else proc_rows
    alive = run_alive(vitals.pid_alive(procs.find_drive(rows, codex, number_of(unit) or -1), state["t0"]),
                      unit_view.run_beat(home, {"run_id": state["run"]}), vitals.files_alive(home, now), now)
    v = _vital(state, derived, frames, hist, alive, now)
    left = step_left(state, hist, home.parent.parent, frames, now)
    tiles = items(state, home, state["step"], v["vital"] in RUNNING, left["r"])
    elapsed = now - state["t0"] if state["t0"] else 0.0
    work = work_before(home, state["t0"]) + elapsed
    runs = make_runs(home, state["run"])
    later = later_steps(state, hist, names, db_rows, unit, runs) if v["vital"] in RUNNING else []
    e = finish(state, left, later, now, work, rework(conn, now)) if v["vital"] in RUNNING else {}
    return card(library, codex, unit, home, state, db_rows, hist, names, derived, v, tiles, e, now, work)


def card(library, codex, unit, home, state, db_rows, hist, names, derived, v, tiles, e, now, work) -> dict:
    """The `models.Progress` dict."""
    step, e = now_step(state, names, tiles), with_left(e, now)
    url, qc = master(library, codex, home) if v["vital"] == "done" else (None, None)
    since = make_start(home, state["t0"])
    made = make_steps(home_timing(home), since)
    looped = loops.loops_text(loops.attempts(db_rows, make_runs(home, state["run"])),
                              loops.borrowed(home_timing(home), since), clock)
    return {"codex": codex, "unit": unit, "run_id": state["run"], "vital": v["vital"], "vital_reason": v["reason"],
            "quiet_s": v["quiet_s"], "budget_s": v["budget_s"], "budget_x": budget_x(v), "run_started": state["t0"],
            "step_started": state["step_t"], "now": now, "elapsed_s": now - state["t0"] if state["t0"] else 0.0,
            "work_s": work, "ceiling_s": float(EPISODE_CEILING_SECONDS), "limit_s": float(OWNER_LIMIT_SECONDS),
            "steps": with_made(with_windows(rail(state, db_rows, hist, names, now), {"steps": e.get("plan")}), made),
            "now_step": step, "items": tiles,
            "inflight_started": inflight_started(state) if counted(state) else None,
            "media_base": f"/thumb/{codex}/160/episodes/{unit}/", "lib_base": f"/lib/{codex}/episodes/{unit}/",
            "eta": e, "trace": [round(t, 1) for t in vitals.trace(derived["signals"], now)],
            "last_words": derived["refusal"] if v["vital"] == "refused" else derived["last_words"],
            "why": derived.get("why", ""), "loops_text": looped,
            "title": title(v["vital"], step, e.get("finish", ""), unit), "master": url, "qc": qc}


# --- the page's helpers (templates and the client share these rules) ---


SHOW_DONE_S = 12 * 3600


def mmss(secs) -> str:
    """`41:07` (or `2:03:09` past an hour) for a loop step's hero."""
    s = max(0, int(secs or 0))
    return f"{s // 3600}:{(s % 3600) // 60:02d}:{s % 60:02d}" if s >= 3600 else f"{s // 60}:{s % 60:02d}"


def budget_x(p: dict, width: float = 240.0) -> float | None:
    """Where the step's stall budget sits on the thirty-minute trace: a signal left
    of this x is older than the budget (panel ruling 5.9); None with no budget."""
    budget = p.get("budget_s")
    if not budget:
        return None
    return round(max(0.0, width - min(float(budget), vitals.TRACE_S) / vitals.TRACE_S * width), 1)


def trace_points(p: dict, width: float = 240.0, base: float = 18.0, top: float = 4.0) -> str:
    """The signal trace's polyline: flat at `base`, a 6 px spike per runner signal
    in the last thirty minutes (x grows to the right, now at the right edge)."""
    xs = sorted(width - (p["now"] - t) / vitals.TRACE_S * width for t in p.get("trace") or [])
    pts = [f"0,{base:g}"]
    for x in xs:
        x = min(max(x, 3.0), width - 3.0)
        pts += [f"{x - 3:.1f},{base:g}", f"{x:.1f},{top:g}", f"{x + 3:.1f},{base:g}"]
    return " ".join(pts + [f"{width:g},{base:g}"])


def shape(p: dict) -> str:
    """What forces a re-render instead of a patch: the vital's kind, the step, the plan's size."""
    step = p.get("now_step") or {}
    group = "run" if p["vital"] in RUNNING else p["vital"]
    return f"{group}|{step.get('id')}|{step.get('kind')}|{len(p.get('items') or [])}"


def range_words(e: dict) -> str:
    """`range 6:15–7:15 pm · 7 steps to run · 9 runs · measured` (progress.js rangeText)."""
    out = []
    if e.get("range") and not e.get("long"):
        out.append(f"range {e['range']}")
    if e.get("firm"):
        out.append(e["firm"])
    if (e.get("rework") or 0) >= 0.005:
        out.append(f"rework +{round(e['rework'] * 100)} % ({e.get('rework_n', 0)} episodes)")
    if e.get("finish"):
        out.append(f"{e['steps_left']} step{'' if e['steps_left'] == 1 else 's'} to run")
    if e.get("n_runs"):
        out.append(f"{e['n_runs']} runs" + (f" · {e['basis']}" if e.get("basis") else ""))
    return " · ".join(out)


def valuetext(p: dict) -> str:
    """The progressbar's words: `take 11 of 26, episode done around 02:45`."""
    step, e = p.get("now_step") or {}, p.get("eta") or {}
    if not step:
        return "no run"
    noun = "take" if step.get("id") == "09" else "panel"
    head = f"{noun} {step['done']} of {step['total']}" if step.get("kind") == "counted" else f"{step['id']} {step['name']}"
    tail = f"episode done around {e['finish']}" if e.get("finish") else ""
    return f"{head}, {tail}" if tail else head


def show(p: dict | None, finished: bool) -> bool:
    """The card shows a run that is running, one that stopped short of a finished
    unit, or a fresh completion (the hand-over to the master); never no run."""
    if not p or p["vital"] == "idle":
        return False
    if p["vital"] == "done":
        return bool(p.get("run_started")) and p["now"] - p["run_started"] < SHOW_DONE_S
    return p["vital"] in RUNNING or not finished
