"""The episode driver: one launcher that resumes, reports and freezes the code.

Ten-agent debate 2026-09-27 (docs/audit/2026-09-27_ep13_ten_agent_plan.md,
fixes #1 and #2).  ep13 took 29 launches and 8 kills; a DEFERRED run sat dead
~90 min until the owner asked "why did you stop??"; five commits landed
between masters of a live episode.  The driver runs `episode.py`, resumes a
DEFERRED run, tells the owner on a stop or a long silence, and refuses to
start on a dirty tree, recording the SHA it ran.  Nobody babysits a run.
"""
from __future__ import annotations

import re
from typing import Callable

MAX_RUNS = 6
"""Runs per drive: a DEFERRED run resumes at its rung; six is five resumes."""
SILENCE_S = 20 * 60
"""A log that has not grown in this long is reported once (ep13: 90 min unseen)."""
LAST_LINES = 12


def outcome(log: str) -> str:
    """completed | deferred | refused | failed, from how the run's log ended."""
    if "EPISODE completed" in log:
        return "completed"
    if re.search(r"DEFERRED: .* needs [\d.]+ s", log):
        return "deferred"            # a budget deferral: the next run resumes at its rung
    if "DEFERRED" in log:
        return "refused"             # a plan deferral waits on a plan fix (ep14: six reruns, ~2.5 h)
    if "REFUSED" in log:
        return "refused"
    return "failed"


def dirty(porcelain: str) -> bool:
    """A tracked change or an untracked file outside library/ (the books are not the code)."""
    return any(line.strip() and not re.match(r"^\?\? library/", line) for line in porcelain.splitlines())


def first_sha(ledger_text: str) -> str | None:
    """The commit the episode STARTED on, from drive.jsonl (five-hour plan
    fix 7: ep14 ran across 23 commits; one episode runs on one commit, and a
    drive on moved code says so out loud)."""
    import json as _json
    for line in ledger_text.splitlines():
        if line.strip():
            try:
                row = _json.loads(line)
            except ValueError:
                continue
            if row.get("sha"):
                return str(row["sha"])
    return None


def silent(last_growth: float, now: float, told: bool) -> bool:
    return not told and now - last_growth >= SILENCE_S


def tail(log: str, n: int = LAST_LINES) -> str:
    return "\n".join(log.strip().splitlines()[-n:])


def drive(run: Callable[[], str], notify: Callable[[str], None], max_runs: int = MAX_RUNS,
          over_budget: Callable[[], bool] = lambda: False) -> int:
    """Run, resume a deferral, stop and tell on anything else; 0 when the
    episode completes.  A SPENT episode is never auto-resumed (five-hour plan
    fix 1): ep14's 31 runs each opened a fresh 5 h."""
    log = ""
    for n in range(1, max_runs + 1):
        log = run()
        got = outcome(log)
        if got == "completed":
            notify(f"episode completed after {n} run(s)")
            return 0
        if got != "deferred":
            notify(f"episode {got} on run {n}:\n{tail(log)}")
            return 1
        if over_budget():
            notify(f"episode ceiling spent after run {n}; not resuming -- the next manual run "
                   f"takes terminals, it does not retake:\n{tail(log)}")
            return 1
    notify(f"episode still deferred after {max_runs} runs:\n{tail(log)}")
    return 1
