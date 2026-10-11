"""Stop at a boundary, never mid-step (C3_verdict #7, T1b, D4).

    autopilot pause --at-boundary   ->  <home>/stop_at_boundary

22 of 23 killed WotW runs (ep19-27) were a session pausing the series to land
a fix, 527 waste-minutes.  The runner reads the flag between steps
(step_runner), between ladder rungs (judged_gate.climbed: every judged step's
ladder, the take ladder's rounds included), between grids (step 07) and
between takes (takes_r2v.collect_all: the take in hand and the one already
running finish, the queued ones are taken off the engine's queue and render
on the resume).  The run exits `paused_at_boundary` with its clock closed; the
next run consumes the flag.  The longest wait is one unit.
"""
from __future__ import annotations

from pathlib import Path

FLAG = "stop_at_boundary"
OUTCOME = "paused_at_boundary"


class PausedAtBoundary(Exception):
    """The flag was read at a boundary: the unit stops here, cleanly."""

    def line(self, label: str) -> str:
        return f"PAUSED AT BOUNDARY | {label} | {self}"


def requested(home) -> bool:
    return home is not None and (Path(home) / FLAG).exists()


def request(home, why: str = "") -> Path:
    path = Path(home) / FLAG
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(why or "pause --at-boundary", encoding="utf-8")
    return path


def consume(home) -> bool:
    """The resume takes the flag away; True when there was one."""
    if not requested(home):
        return False
    (Path(home) / FLAG).unlink(missing_ok=True)
    return True


def check(home, where: str) -> None:
    """Raise PausedAtBoundary when the flag is set: the caller is at a boundary."""
    if requested(home):
        raise PausedAtBoundary(where)
