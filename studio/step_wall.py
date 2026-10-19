"""The step wall (owner 2026-10-18): every step of the episode line runs under a timer.

On entry the step says so -- a timestamped `STEP <id> start` line in the run's log and a
`started` row in timing.jsonl -- so a step killed mid-run is still on the record
(STEP_CAPS.md finding 4: Jekyll ep01's plan ran 47 min and timing.jsonl held nothing).
The wall is the step's rows of the cap table summed (studio/step_caps).  A call in flight is
never cut: the wall is read at the safe boundaries -- before a ladder's next rung
(studio/judged_gate) and when the step ends, where an overrun is logged as a CAP line.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable

from studio import step_caps


@dataclass
class StepWall:
    step_id: str
    wall_s: float
    started: float
    clock: Callable[[], float] = field(default=time.time)
    prior: float = 0.0
    """Seconds earlier runs of this step already spent (a relaunch never resets the wall)."""

    def elapsed(self) -> float:
        return self.prior + self.clock() - self.started

    def this_run(self) -> float:
        return self.clock() - self.started

    def spent(self) -> bool:
        return self.wall_s > 0 and self.elapsed() >= self.wall_s


def seattle(epoch: float) -> str:
    """HH:MM:SS PDT/PST: the owner reads every time in Seattle's."""
    try:
        from zoneinfo import ZoneInfo
        at = datetime.fromtimestamp(epoch, ZoneInfo("America/Los_Angeles"))
        return at.strftime("%H:%M:%S %Z")
    except Exception:                                  # noqa: BLE001 -- no tz database: the box's own
        return datetime.fromtimestamp(epoch).strftime("%H:%M:%S")


def started_row(ctx, step_id: str, at: float) -> None:
    """A zero-second `started` row in the unit's timing.jsonl (every summing reader adds 0)."""
    if getattr(ctx, "stage", "") != step_caps.STAGE or getattr(ctx, "number", None) is None:
        return
    from studio import episode_clock
    path = episode_clock.path(ctx.book_dir, ctx.number)
    stamp = datetime.fromtimestamp(at).isoformat(timespec="seconds")
    row = {"stage": f"step_{step_id}", "started": stamp, "ended": stamp, "seconds": 0.0,
           "ok": True, "note": "started", "event": "started"}
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")


def wall_key(step_id: str) -> str:
    return f"wall.{step_id}"


def home_of(ctx):
    """The episode folder: the context's own, else derived from the book and the number."""
    home = getattr(ctx, "home", None)
    if home is not None or getattr(ctx, "stage", "") != step_caps.STAGE or getattr(ctx, "number", None) is None:
        return home
    from studio import episode_home
    return episode_home.home(ctx.book_dir, ctx.number)


def prior_seconds(ctx, step_id: str) -> float:
    """What earlier runs of this step spent this episode (episodes/epNN/attempts.json)."""
    from studio import step_attempts
    home = home_of(ctx)
    return step_attempts.seconds(home, wall_key(step_id)) if home is not None else 0.0


def open_wall(ctx, step) -> StepWall:
    """The step's wall, started from what its earlier runs spent, said and written down."""
    clock = getattr(ctx, "clock", None) or time.time
    wall_s = step_caps.step_wall_s(step.STEP_ID) if getattr(ctx, "stage", "") == step_caps.STAGE else 0.0
    wall = StepWall(step.STEP_ID, wall_s, clock(), clock, prior_seconds(ctx, step.STEP_ID))
    before = f", {step_caps.mmss(wall.prior)} spent before" if wall.prior else ""
    line = (f"STEP {step.STEP_ID} start {seattle(wall.started)} "
            f"({step.NAME}, wall {step_caps.mmss(wall_s)}{before})")
    print(line, flush=True)
    ctx.log(line, step_id=step.STEP_ID)
    started_row(ctx, step.STEP_ID, wall.started)
    return wall


def record_spent(ctx, wall: StepWall) -> None:
    """This run's seconds onto the step's episode total -- on success AND on a failure."""
    from studio import step_attempts
    home = home_of(ctx)
    if home is not None:
        step_attempts.spend(home, wall_key(wall.step_id), round(wall.this_run(), 1))


def close_wall(ctx, wall: StepWall) -> None:
    """A step that ran past its wall is said as a CAP line; the run goes on."""
    if not wall.spent():
        return
    line = step_caps.cap_line(f"step {wall.step_id}", 1, 1, wall.elapsed(), 0) + \
        f" -- over its {step_caps.mmss(wall.wall_s)} wall"
    print(line, flush=True)
    ctx.log(line, step_id=wall.step_id, level="WARNING")
