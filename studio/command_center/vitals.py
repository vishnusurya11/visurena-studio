"""Is the run alive? (progress tracker spec §7.)  Pure functions; the checks
run in priority order and the first match wins:

    done      the run's end says completed
    dead      a crash, or no drive process that started before the run did
    refused / deferred   the run ended so (the reason is the runner log's refusal)
    stalled   alive, but quiet longer than the step's budget
    quiet     alive, quiet more than a minute
    live      otherwise

Only runner signals count toward "quiet" (the runner log, the drive log the
runner writes, a take landing); a file somebody else touched never does."""
from __future__ import annotations

from studio import eta

QUIET_S, PLAN_BUDGET_S, MIN_BUDGET_S, TRACE_S, SLACK_S = 60.0, 600.0, 600.0, 1800.0, 5.0


def pid_alive(proc, run_t0: float | None) -> bool:
    """A drive process exists and started no later than the run began (a later
    one is another launch, or a reused id)."""
    if proc is None:
        return False
    return run_t0 is None or proc.started is None or proc.started <= run_t0 + SLACK_S


def step_budget(step: str | None, frames: int = 0, first: bool = False, history: dict | None = None) -> float:
    """How long a step may stay silent: twice the take's prior on the shoot (with
    the cold load on the first take), ten minutes on the plan, else twice the norm."""
    if step == "09" and frames:
        return 2 * eta.take_prior(frames) + (eta.TAKE_COLD if first else 0.0)
    if step == "02":
        return PLAN_BUDGET_S
    xs = (history or {}).get(step or "", [])
    return max(MIN_BUDGET_S, 2 * eta.band(xs)[1]) if xs else 2 * MIN_BUDGET_S


def quiet_seconds(signals: list[float], now: float) -> float | None:
    """Seconds since the newest runner signal; None with none."""
    return max(0.0, now - max(signals)) if signals else None


def trace(signals: list[float], now: float) -> list[float]:
    """The signals of the last thirty minutes, for the signal trace."""
    return [t for t in signals if now - TRACE_S <= t <= now + SLACK_S]


def minutes(secs: float) -> str:
    """`22m`, or `45s` under a minute."""
    return f"{secs / 60:.0f}m" if secs >= 60 else f"{secs:.0f}s"


FILES_ALIVE_S = 45 * 60


def files_alive(home, now: float) -> bool:
    """The unit's folder or a child dir moved recently: the run writes, so it
    lives, whether or not its process answers the API (ep23, 2026-10-07)."""
    from pathlib import Path
    home = Path(home)
    if not home.is_dir():
        return False
    stamps = [home.stat().st_mtime] + [d.stat().st_mtime for d in home.iterdir() if d.is_dir()]
    return any(now - s < FILES_ALIVE_S for s in stamps)


def vital(state: dict, alive: bool, quiet_s: float | None, budget_s: float, reason: str = "") -> dict:
    """{vital, reason} for the folded state, the process check and the silence."""
    outcome = state.get("outcome")
    if outcome == "completed":
        return {"vital": "done", "reason": "completed"}
    if outcome == "failed" or (not alive and outcome is None):
        return {"vital": "dead", "reason": reason or ("the run crashed" if outcome else "no drive process")}
    if outcome in ("refused", "deferred", "escalated"):
        return {"vital": "deferred" if outcome == "deferred" else "refused", "reason": reason or outcome}
    q = quiet_s or 0.0
    if q > budget_s:
        return {"vital": "stalled", "reason": f"quiet {minutes(q)} · budget {minutes(budget_s)}"}
    if q > QUIET_S:
        return {"vital": "quiet", "reason": f"quiet {minutes(q)}"}
    return {"vital": "live", "reason": ""}
