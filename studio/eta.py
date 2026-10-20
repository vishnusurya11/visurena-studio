"""Elapsed time and the ETA of an episode run (progress tracker spec §2).

Pure functions over measured history; `now` is always passed in and no ETA
logic runs in the browser.  Elapsed is a fact; the finish is a band:

- a step's norm is the started->completed pairs of ONE run in the `events`
  table, over the last eight episodes (`step_history`), banded p10/p50/p90;
- a counted step (the takes) is a frame-weighted prior corrected by an EWMA
  of measured/prior, seeded at 0.75 (recent takes ran 173-209 s against a
  modelled 262 s); the take in flight pulls the pace up once it overruns, so
  the finish never rises when a take lands;
- a loop step (the plan, QC, a ladder) has no count: what is left is the
  median of the history still above the elapsed time, and nothing past p90
  ("running long");
- the episode's band is the root of summed variances (IQR-derived sigma per
  step), capped at the five-hour ceiling."""
from __future__ import annotations

import math
import sqlite3
import statistics
from datetime import datetime, tzinfo
from fnmatch import fnmatch

from studio.episode_clock import TAKE_COLD, TAKE_FIXED, TAKE_PER_FRAME

SEED, ALPHA, MEASURED_AFTER = 0.75, 0.3, 3
ROUND_S = 300.0
FULL_RUN = 0.25
"""A pair under this share of its step's p90 is a resume that kept the work (page experts 2026-10-18)."""
SUB_STEP = {"plan": "02", "places": "03", "sheets": "03", "cast": "03", "lines": "04", "timeline": "05",
            "respot": "05", "prompts": "06", "no_last_frame": "06", "grids": "07", "panels": "08",
            "panel_dq": "08", "panel_content": "08", "panel_eye": "08", "takes": "09", "take_render": "09", "take_dq": "09",
            "take_content": "09", "take_eye": "09", "strip": "09", "assemble": "10", "upscale": "10", "qc": "11",
            "master_eye": "11", "dossier": "12"}
"""timing.jsonl's stage names (the `timed` subs) under the episode step that runs them."""


# --- time ---


def to_epoch(ts, tz: tzinfo | None = None) -> float | None:
    """A stamp as UTC epoch seconds: a number as is, an ISO stamp with a zone
    as written, a naive one (timing.jsonl's local time) in `tz` (default: this
    machine's zone); None for junk."""
    if isinstance(ts, (int, float)):
        return float(ts)
    try:
        d = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
    except ValueError:
        return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=tz) if tz else d.astimezone()
    return d.timestamp()


def round_to(epoch: float, step: float = ROUND_S) -> float:
    """The finish time the page shows: to the nearest five minutes."""
    return math.floor(epoch / step + 0.5) * step


# --- bands ---


def band(xs) -> tuple[float, float, float]:
    """(p10, p50, p90) of a history; one value is itself, none is zeros."""
    xs = sorted(float(x) for x in xs)
    if len(xs) < 2:
        return (xs[0],) * 3 if xs else (0.0, 0.0, 0.0)
    q = statistics.quantiles(xs, n=10, method="inclusive")
    return (q[0], q[4], q[8])


def sigma(xs) -> float:
    """An IQR-derived standard deviation (IQR / 1.349); 0 below two values."""
    xs = sorted(float(x) for x in xs)
    if len(xs) < 2:
        return 0.0
    q = statistics.quantiles(xs, n=4, method="inclusive")
    return (q[2] - q[0]) / 1.349


def confidence(xs) -> str:
    """Fewer than five runs is an estimate, five or more is measured."""
    return "measured" if len(xs) >= 5 else "estimate"


def mad(xs) -> float:
    """The median absolute deviation; 0 below two values."""
    if len(xs) < 2:
        return 0.0
    mid = statistics.median(xs)
    return statistics.median(abs(x - mid) for x in xs)


# --- history ---


def _pairs(rows) -> list[tuple[str, str, float]]:
    """(unit, step, seconds) for each started->completed pair inside one run."""
    began, out = {}, []
    for ts, step, event, run, unit in rows:
        key = (run, step)
        if event == "started":
            began[key] = to_epoch(ts)
        elif event == "completed" and began.get(key) is not None and to_epoch(ts) is not None:
            out.append((unit, step, to_epoch(ts) - began.pop(key)))
    return out


def _recent(units: list[str], n: int) -> set[str]:
    """The last n distinct units in the order they were last seen."""
    seen: dict[str, int] = {}
    for i, unit in enumerate(units):
        seen[unit] = i
    return set(sorted(seen, key=seen.get)[-n:])


def step_history(conn: sqlite3.Connection, stage: str = "episode",
                 last_n_episodes: int = 8) -> dict[str, list[float]]:
    """{step: [seconds]} from the `events` table: same-run pairs only, the last n episodes."""
    rows = conn.execute("SELECT event_ts, step_id, event, run_id, unit FROM events WHERE stage = ?"
                        " AND event IN ('started', 'completed') ORDER BY id", (stage,)).fetchall()
    pairs = _pairs([tuple(r) for r in rows])
    keep = _recent([u for u, _, _ in pairs], last_n_episodes)
    out: dict[str, list[float]] = {}
    for unit, step, secs in pairs:
        if unit in keep:
            out.setdefault(step, []).append(round(secs, 1))
    return out


def full_runs(xs, frac: float = FULL_RUN) -> list[float]:
    """The pairs that did the step's work: at least `frac` x p90 of the history (a resume
    that found its outputs lands in seconds and drops out); all of xs when none would stay."""
    xs = list(xs)
    if len(xs) < 2:
        return xs
    floor = frac * band(xs)[2]
    return [x for x in xs if x >= floor] or xs


REWORK_PRIOR = 0.15
"""The measured median rework share of the published WotW episodes (timeline debate 2026-10-18)."""
FIRM_EPISODES, FIRM_SPREAD_S = 5, 30 * 60


REWORK_LAST_N = 9
"""The norm is the most recent delivered units: rework fell from 90-320 % (September) to 0-17 %."""


def finished_units(conn: sqlite3.Connection, stage: str = "episode", last_n: int | None = None) -> set[str]:
    """`codex/unit` of the units a run delivered (step 12 completed), the last_n most recent."""
    rows = conn.execute("SELECT codex_id, unit FROM events WHERE stage = ? AND step_id = '12'"
                        " AND event = 'completed' GROUP BY codex_id, unit ORDER BY MAX(event_ts) DESC"
                        + (" LIMIT ?" if last_n else ""), (stage, last_n) if last_n else (stage,))
    return {f"{c}/{u}" for c, u in rows}


def episode_pairs(conn: sqlite3.Connection, stage: str = "episode") -> list[tuple[str, str, float]]:
    """(codex/unit, step, seconds) of every same-run step pair, in event order (a unit name
    repeats across books, so the key carries the codex)."""
    rows = conn.execute("SELECT event_ts, step_id, event, run_id, codex_id || '/' || unit FROM events"
                        " WHERE stage = ? AND event IN ('started', 'completed') ORDER BY id", (stage,))
    return _pairs([tuple(r) for r in rows])


def rework_shares(pairs, finished: set[str]) -> list[float]:
    """Per finished unit: its repeat step time over its one full pass -- each step's LONGEST
    pair (a first pair can be a resume that found its outputs in seconds, 2026-10-18)."""
    longest: dict[tuple[str, str], float] = {}
    total: dict[str, float] = {}
    for unit, step, secs in pairs:
        if unit in finished:
            total[unit] = total.get(unit, 0.0) + secs
            longest[(unit, step)] = max(longest.get((unit, step), 0.0), secs)
    once: dict[str, float] = {}
    for (unit, _), secs in longest.items():
        once[unit] = once.get(unit, 0.0) + secs
    return [total[u] / once[u] - 1.0 for u in total if once.get(u)]


def rework_band(shares, prior: float = REWORK_PRIOR) -> tuple[float, float, int]:
    """(median, 80th percentile, n) of the rework shares; the prior below three units."""
    xs = sorted(shares)
    if len(xs) < 3:
        return (prior, 2 * prior, len(xs))
    return (statistics.median(xs), statistics.quantiles(xs, n=10, method="inclusive")[7], len(xs))


def with_rework(p: dict, now: float, band: tuple[float, float, int], ceiling_at: float) -> dict:
    """The projection with relaunch rework on the time left: p50 x (1 + median share), the high
    end x (1 + p80 share), the low end the clean first pass; all under the ceiling."""
    left, (p50, p80, n) = max(0.0, p["finish_at"] - now), band
    mid, hi = now + left * (1 + p50), now + left * (1 + p80)
    return {**p, "lo": min(p["finish_at"], ceiling_at), "finish_at": min(mid, ceiling_at),
            "hi": min(hi, ceiling_at), "capped": bool(p.get("capped")) or hi > ceiling_at,
            "rework": p50, "rework_n": n}


def firmness(n_units: int, long: bool, spread_s: float) -> str:
    """`firm` with enough finished units, a step inside its measured runs and a tight band."""
    return "firm" if n_units >= FIRM_EPISODES and not long and spread_s < FIRM_SPREAD_S else "rough"


def sub_norm(files: list[list[dict]], subs) -> float:
    """Σ over `subs` of the median seconds timing.jsonl measured for each."""
    total = 0.0
    for sub in subs:
        xs = [float(r.get("seconds") or 0) for rows in files for r in rows if r.get("stage") == sub]
        total += statistics.median(xs) if xs else 0.0
    return total


def timing_history(files: list[list[dict]]) -> dict[str, list[float]]:
    """{step: [seconds per episode file]} from timing.jsonl rows -- the
    fallback norm for a step the events table has too few pairs of."""
    out: dict[str, list[float]] = {}
    for rows in files:
        per: dict[str, float] = {}
        for r in rows:
            step = SUB_STEP.get(str(r.get("stage")))
            if step:
                per[step] = per.get(step, 0.0) + float(r.get("seconds") or 0)
        for step, secs in per.items():
            out.setdefault(step, []).append(round(secs, 1))
    return out


# --- counted steps: the takes ---


def take_prior(frames: int, cold: bool = False) -> float:
    """The modelled seconds of one take (episode_clock's least squares)."""
    return TAKE_FIXED + TAKE_PER_FRAME * frames + (TAKE_COLD if cold else 0.0)


def pace(ratios, seed: float = SEED, alpha: float = ALPHA) -> float:
    """The EWMA of measured/prior over the run's landed takes, from the seed."""
    r = seed
    for x in ratios:
        r = alpha * x + (1 - alpha) * r
    return r


def _priors(done, remaining, cold_paid: bool) -> tuple[list[float], list[float]]:
    """The priors of the landed and the remaining takes; the run's first take pays the cold load."""
    cold = not cold_paid
    ps_done = [take_prior(f, cold=cold and i == 0) for i, (_, f) in enumerate(done)]
    ps_left = [take_prior(f, cold=cold and not done and i == 0) for i, f in enumerate(remaining)]
    return ps_done, ps_left


def take_remaining(done, remaining, cold_paid: bool, inflight_s: float | None = None) -> dict:
    """Seconds left for the takes: `done` is [(secs, frames)], `remaining` is
    frames with the take in flight first when `inflight_s` is given."""
    ps_done, ps_left = _priors(done, remaining, cold_paid)
    ratios = [s / p for (s, _), p in zip(done, ps_done) if p > 0]
    r = pace(ratios)
    if inflight_s is not None and ps_left and inflight_s / ps_left[0] > r:
        r = ALPHA * (inflight_s / ps_left[0]) + (1 - ALPHA) * r
    secs = r * sum(ps_left)
    if inflight_s is not None and ps_left:
        secs -= min(inflight_s, r * ps_left[0])
    spread = 1.4826 * mad(ratios) * (statistics.mean(ps_left) if ps_left else 0) * math.sqrt(len(ps_left))
    return {"secs": max(secs, 0.0), "spread": spread, "r": r,
            "basis": "measured" if len(done) >= MEASURED_AFTER else "norm"}


# --- loop steps ---


def remaining_unknown(elapsed: float, xs) -> float | None:
    """The median of what the history has left above `elapsed`; None past p90
    (the page says "running long") or with no history at all."""
    if not xs or elapsed > band(xs)[2]:
        return None
    left = [x - elapsed for x in xs if x > elapsed]
    return statistics.median(left) if left else 0.0


# --- the episode ---


def episode_eta(now: float, running_left: float | None, running_sigma: float,
                later: list[list[float]], ceiling_at: float) -> dict:
    """The finish (p50) with a band of √Σσ², capped at the ceiling; no finish
    when the running step is past its p90."""
    if running_left is None:
        return {"finish_at": None, "lo": None, "hi": None, "long": True, "capped": False}
    p50 = now + running_left + sum(band(xs)[1] for xs in later)
    sd = math.sqrt(running_sigma ** 2 + sum(sigma(xs) ** 2 for xs in later))
    hi, capped = p50 + sd, p50 + sd > ceiling_at
    return {"finish_at": min(p50, ceiling_at), "lo": max(now, min(p50 - sd, ceiling_at)),
            "hi": min(hi, ceiling_at), "long": False, "capped": capped}


# --- the projection: every step's window (page experts 2026-10-18, rules W, D, B) ---


def globs_meet(a: str, b: str) -> bool:
    """Two book-relative paths or globs that can name the same file."""
    return fnmatch(a, b) or fnmatch(b, a)


def will_run(order: list[str], running: str, kept: set[str], ins: dict, outs: dict) -> dict[str, bool]:
    """{step: runs again} for the steps after `running` (rule W): a step no run ever
    finished, or one whose inputs meet what a step running in this run writes."""
    after = order[order.index(running) + 1:] if running in order else list(order)
    dirty, out = list(outs.get(running, [])), {}
    for sid in after:
        out[sid] = sid not in kept or any(globs_meet(i, o) for i in ins.get(sid, []) for o in dirty)
        if out[sid]:
            dirty += outs.get(sid, [])
    return out


def _window(sid: str, runs: bool, start: float, p50: float, sd: float) -> dict:
    """One later step's projected start->end with its band; a kept step has none."""
    if not runs:
        return {"id": sid, "will_run": False, "start_at": None, "end_at": None, "lo": None, "hi": None}
    end = start + p50
    return {"id": sid, "will_run": True, "start_at": start, "end_at": end, "lo": end - sd, "hi": end + sd}


def project(now: float, running_left: float | None, running_sigma: float,
            later: list[tuple[str, bool, list[float]]], ceiling_at: float) -> dict:
    """Each later step's window and the episode's finish (rule B): `later` is
    [(step, will run, full-run history)], chained on p50s with √Σσ² bands; past the
    running step's p90 (`running_left` None) the finish is a floor, flagged long."""
    t, var, steps = now + (running_left or 0.0), running_sigma ** 2, []
    for sid, runs, xs in later:
        p50 = band(xs)[1] if runs and xs else 0.0
        var += sigma(xs) ** 2 if runs else 0.0
        steps.append(_window(sid, runs, t, p50, math.sqrt(var)))
        t += p50
    sd = math.sqrt(var)
    return {"steps": steps, "finish_at": min(t, ceiling_at), "lo": max(now, min(t - sd, ceiling_at)),
            "hi": min(t + sd, ceiling_at), "capped": t + sd > ceiling_at, "long": running_left is None,
            "step_end_at": now + running_left if running_left is not None else None,
            "steps_left": sum(1 for s in steps if s["will_run"])}


# --- owed units: charge only what is still to do (Jekyll Kawajiri ep01, 2026-10-19) ---

OWED_LO, OWED_HI = 0.6, 1.5
"""Until per-take seconds are measured the owed time is a band: 60 % to 150 % of the prior."""
HARD_STOP_S = 6 * 3600.0
"""The owner's <= 6 h of machine work per episode (memory: five-hour episode)."""


def owed_eta(owed_frames: list[int], done: list[tuple[float, int]], now: float, work_s: float,
             cold_paid: bool = True, limit_s: float = HARD_STOP_S) -> dict:
    """The seconds the owed takes still cost as a band, and the 6 h hard stop: `done` is the
    run's [(secs, frames)] landings, `owed_frames` only the units to check, fix or redo."""
    t = take_remaining(done, owed_frames, cold_paid=cold_paid)
    measured = t["basis"] == "measured"
    lo = max(0.0, t["secs"] - t["spread"]) if measured else t["secs"] * OWED_LO
    hi = t["secs"] + t["spread"] if measured else t["secs"] * OWED_HI
    stop = now + max(0.0, limit_s - work_s)
    return {"lo_s": lo, "mid_s": t["secs"], "hi_s": hi, "basis": "measured" if measured else "estimate",
            "hard_stop_at": stop, "over": bool(owed_frames) and now + hi > stop}


def left_for_step(step_left: float | None, owed: dict | None) -> float | None:
    """The time left: the owed units' median when unit state exists, else the step-level guess."""
    return owed["mid_s"] if owed is not None else step_left


def _hours(secs: float) -> str:
    m = int(max(0.0, secs) // 60)
    return f"{m // 60}h{m % 60:02d}"


def hard_stop_words(stop_at: float, work_s: float, clock) -> str:
    """`hard stop 9:40 pm · 5h00 of 6h used`: the 6 h line as a time of day."""
    return f"hard stop {clock(stop_at)} · {_hours(work_s)} of {int(HARD_STOP_S // 3600)}h used"


def flagged_words(rows: list[dict]) -> str:
    """`2 flagged takes ship, 5.5 s total` from work_r2v/flagged_takes.json (contract K7)."""
    if not rows:
        return ""
    secs = sum(float(r.get("seconds_in_master") or 0.0) for r in rows)
    n = len(rows)
    return f"{n} flagged take{' ships' if n == 1 else 's ship'}, {secs:.1f} s total"


def fixes_words(n: int) -> str:
    """`4 fixes waiting for the next pause`: commits on master after the running sha."""
    return f"{n} fix{'' if n == 1 else 'es'} waiting for the next pause" if n > 0 else ""
