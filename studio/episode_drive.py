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


ERROR_LINE = re.compile(r"^((?:\w+\.)*\w*(?:Error|Exception|OverBudget|Exit)):")
"""A `<Class>: <why>` line: a traceback's last line, or the wall's own printed one."""


def outcome(log: str) -> str:
    """completed | overbudget | escalated | deferred | refused | failed, from
    how the run's log ended.  The autopilot (2026-10-06) classifies by this
    word: ep19's stop at the $3 wall read `failed`, the same as a crash, and
    the only evidence was prose in the log's tail.  Money and an owner gate
    are read BEFORE the broad words: a plan deferral the wall caused (the
    ladder's caught form) is still the wall."""
    if "EPISODE completed" in log:
        return "completed"
    if "OverBudget" in log:
        return "overbudget"
    if re.search(r"^OWNER ", log, re.MULTILINE):
        return "escalated"
    if re.search(r"DEFERRED: .* needs [\d.]+ s", log):
        # HISTORICAL DRIVE LOGS ONLY: judged_gate no longer emits
        # 'DEFERRED: ... needs ... s' -- a spent clock is terminal in the
        # same run (five-hour verdict).  The regex stays so old logs read
        # as what they were.
        return "deferred"
    if "DEFERRED" in log:
        return "refused"             # a plan deferral waits on a plan fix (ep14: six reruns, ~2.5 h)
    if "REFUSED" in log:
        return "refused"
    return "failed"


def error_class(log: str) -> str | None:
    """The exception class the run ended on -- the LAST `<Class>: ...` line of
    the log -- so the drive ledger carries a word the supervisor matches, never
    prose it parses (autopilot 2026-10-06; ep19's `studio.llm.OverBudget`)."""
    for line in reversed(log.splitlines()):
        if found := ERROR_LINE.match(line.strip()):
            return found.group(1)
    return None


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
