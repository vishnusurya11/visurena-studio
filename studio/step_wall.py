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
import threading
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
    order: bool = False
    """An owner-ordered redo run: its seconds are wall.<id>.order, the cure cap never sees them."""
    heart: object = None

    def elapsed(self) -> float:
        return self.prior + (0.0 if self.order else self.this_run())

    def this_run(self) -> float:
        return self.clock() - self.started

    def spent(self) -> bool:
        return self.wall_s > 0 and self.elapsed() >= self.wall_s


def deadline_of(wall: StepWall) -> float | None:
    """The epoch second this step's wall ends at, or None (no wall, or already spent: the CAP line speaks)."""
    left = wall.wall_s - wall.elapsed()
    return wall.clock() + left if wall.wall_s > 0 and left > 0 else None


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


BEAT_S = 60.0
"""How often a running step writes its live seconds (a kill leaves at most this much uncharged)."""


def _bucket(step_id: str, order: bool) -> str:
    return wall_key(step_id) + (".order" if order else "")


def beat(home, step_id: str, seconds: float, order: bool = False) -> None:
    """This run's absolute seconds so far, as wall.<id>[.order].live (replaced, never added)."""
    from studio import step_attempts
    step_attempts.set_seconds(home, _bucket(step_id, order) + ".live", seconds)


def fold(home, step_id: str) -> float:
    """A run that died left a live row: its seconds join the booked wall, the row is cleared."""
    from studio import step_attempts
    total = 0.0
    for order in (False, True):
        key = _bucket(step_id, order)
        live = step_attempts.seconds(home, key + ".live")
        if live:
            step_attempts.add_seconds(home, key, live)
            total += live
        step_attempts.drop(home, key + ".live")
    return total


def charged(home, step_id: str) -> float:
    """Everything the step cost the 6 h clock: first pass and owner order, booked and live."""
    from studio import step_attempts
    return round(sum(step_attempts.elapsed(home, _bucket(step_id, o)) for o in (False, True)), 1)


def ledger(home) -> dict:
    """{step_id: {charged, wall}} for every step with a booked or live wall: what the 6 h clock
    was charged (first pass, owner order, live heartbeat) against the step's cap-table wall."""
    from studio import step_attempts
    ids = {k.split(".")[1] for k in step_attempts.read(home) if k.startswith("wall.")}
    return {i: {"charged": charged(home, i), "wall": step_caps.step_wall_s(i)} for i in sorted(ids)}


class Heartbeat(threading.Thread):
    """Writes the wall's live seconds every `every` s until stopped; a failed write is skipped."""

    def __init__(self, home, wall: StepWall, every: float = BEAT_S):
        super().__init__(daemon=True, name=f"wall-beat-{wall.step_id}")
        self.home, self.wall, self.every = home, wall, every
        self._stop_evt = threading.Event()

    def run(self) -> None:
        while not self._stop_evt.wait(self.every):
            try:
                beat(self.home, self.wall.step_id, self.wall.this_run(), self.wall.order)
            except Exception:                              # noqa: BLE001 -- a beat never fails the step
                pass

    def stop(self) -> None:
        self._stop_evt.set()
        if self.is_alive():
            self.join(timeout=5)


def prior_seconds(ctx, step_id: str) -> float:
    """What earlier runs of this step spent this episode (episodes/epNN/attempts.json)."""
    from studio import step_attempts
    home = home_of(ctx)
    return step_attempts.seconds(home, wall_key(step_id)) if home is not None else 0.0


def _ordered(home, step_id: str) -> bool:
    """True only for a recorded owner redo (K12); a flag on the context is not a record."""
    from studio import work_orders
    return home is not None and work_orders.recorded(home, step_id)


def open_wall(ctx, step) -> StepWall:
    """The step's wall, started from what its earlier runs spent, said and written down."""
    clock = getattr(ctx, "clock", None) or time.time
    home = home_of(ctx)
    if home is not None:
        fold(home, step.STEP_ID)                         # a killed run is charged before this one opens
    wall_s = step_caps.step_wall_s(step.STEP_ID) if getattr(ctx, "stage", "") == step_caps.STAGE else 0.0
    wall = StepWall(step.STEP_ID, wall_s, clock(), clock, prior_seconds(ctx, step.STEP_ID),
                    order=_ordered(home, step.STEP_ID))
    before = f", {step_caps.mmss(wall.prior)} spent before" if wall.prior else ""
    after = ", owner order" if wall.order else ""
    line = (f"STEP {step.STEP_ID} start {seattle(wall.started)} "
            f"({step.NAME}, wall {step_caps.mmss(wall_s)}{before}{after})")
    print(line, flush=True)
    ctx.log(line, step_id=step.STEP_ID)
    started_row(ctx, step.STEP_ID, wall.started)
    if home is not None:
        wall.heart = Heartbeat(home, wall)
        wall.heart.start()
    return wall


def book(home, wall: StepWall, order: bool) -> None:
    """This run's seconds onto the booked bucket, and its live row off (never counted twice)."""
    from studio import step_attempts
    step_attempts.spend(home, _bucket(wall.step_id, order), round(wall.this_run(), 1))
    step_attempts.drop(home, _bucket(wall.step_id, order) + ".live")


def record_spent(ctx, wall: StepWall) -> None:
    """This run's seconds onto the step's episode total -- on success AND on a failure."""
    if wall.heart is not None:
        wall.heart.stop()
    home = home_of(ctx)
    if home is not None:
        book(home, wall, wall.order)


def close_wall(ctx, wall: StepWall) -> None:
    """A step that ran past its wall is said as a CAP line; the run goes on."""
    if not wall.spent():
        return
    line = step_caps.cap_line(f"step {wall.step_id}", 1, 1, wall.elapsed(), 0) + \
        f" -- over its {step_caps.mmss(wall.wall_s)} wall"
    print(line, flush=True)
    ctx.log(line, step_id=wall.step_id, level="WARNING")
