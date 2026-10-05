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

from studio.episode_clock import TAKE_COLD, TAKE_FIXED, TAKE_PER_FRAME

SEED, ALPHA, MEASURED_AFTER = 0.75, 0.3, 3
ROUND_S = 300.0
SUB_STEP = {"plan": "02", "places": "03", "sheets": "03", "cast": "03", "lines": "04", "timeline": "05",
            "respot": "05", "prompts": "06", "no_last_frame": "06", "grids": "07", "panels": "08",
            "panel_dq": "08", "panel_content": "08", "panel_eye": "08", "takes": "09", "take_dq": "09",
            "take_content": "09", "take_eye": "09", "strip": "09", "assemble": "10", "qc": "11",
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
