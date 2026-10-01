"""The time ceiling of an unattended trailer run.

Nothing in the trailer chain spends money -- MiniMax Music 3, MiniMax-H3 and
Qwen3-TTS all run on the local ComfyUI -- so the one budget is wall-clock.
Each step owns a SHARE of the ceiling; unused time rolls forward, an
overrun is absorbed by the ceiling, which binds last.  A step asks
`can_afford` before every render; a "no" means "take the terminal rung".
"""
from __future__ import annotations

import time
from typing import Callable

TRAILER_CEILING_SECONDS = 6 * 3600

TRAILER_SHARES: dict[str, float] = {
    "01": 5 / 360, "02": 40 / 360, "03": 30 / 360, "04": 10 / 360,
    "05": 15 / 360, "06": 5 / 360, "07": 210 / 360, "08": 10 / 360,
    "09": 15 / 360, "10": 5 / 360, "slack": 15 / 360,
}
"""Minutes of the 360, as fractions (BLUEPRINT.md, Time shares)."""

EPISODE_CEILING_SECONDS = 5 * 3600
"""The render approval, as the thing it protected: the owner's GPU hours.
18 000 s against today's 3.5-4 h episode (decision 2026-09-24-automate-the-
taste-gates, cost); `RENDER_HOLD` stays the brake."""

EPISODE_SHARES: dict[str, float] = {
    "01": 3 / 300, "02": 8 / 300, "03": 6 / 300, "04": 6 / 300, "05": 2 / 300,
    "06": 3 / 300, "07": 4 / 300, "08": 60 / 300, "09": 125 / 300, "10": 8 / 300,
    "11": 8 / 300, "12": 2 / 300,
    "judges": 15 / 300, "ladders": 50 / 300, "slack": 0 / 300,
}
# RE-PRICED 2026-09-27 from ep13's clock: step 08 spent ~15 min on the content read
# and ~13 min on the judge's reads per pass -- 28 min of a 20-min share, so every run
# deferred before one redraw rung.  08 now holds its reads plus one full rung; the
# takes keep 125 min (ep13 asked 7176 s); places and lines are mostly cached (6 each).
"""Minutes of the 300, as fractions, keyed by episode step id; the judges
(capped at 15 GPU min) and the ladders (60 min: panels 10, takes 40, master
retake 10) hold shares of their own.  Unused time rolls forward."""


class Budget:
    """Wall-clock shares per step, rolling forward, under one ceiling."""

    def __init__(self, ceiling_seconds: float, shares: dict[str, float],
                 clock: Callable[[], float] = time.monotonic):
        self.ceiling = ceiling_seconds
        self.shares = shares
        self.clock = clock
        self.t0 = clock()
        self.step: str | None = None
        self.step_started = self.t0
        self.carry = 0.0          # unused time from earlier steps
        self.pool_drawn = 0.0     # the `ladders` share drawn by rungs

    def charge(self, spent: float) -> None:
        """Seconds earlier RUNS of this episode already spent (timing.jsonl):
        the ceiling covers the episode, not the process.  ep14's 31 driver
        runs each opened a fresh 5 h (five-hour plan fix 1, 2026-09-30)."""
        self.t0 -= max(0.0, spent)

    def ceiling_spent(self) -> bool:
        """The episode's whole ceiling is gone: no rung can ever be paid for
        again, so a refusal here is TERMINAL, never a deferral."""
        return self.clock() - self.t0 >= self.ceiling

    def start(self, step: str) -> None:
        """Close the running step, carry its balance, open `step`."""
        if step not in self.shares:
            raise KeyError(f"no time share for step {step!r}")
        if self.step is not None:
            # UNUSED time rolls forward; an OVERRUN is not charged to the next
            # step -- the ceiling alone binds it (ep13: 08's 1034 s overrun
            # refused the takes twice, after 08 had signed; speed plan #3).
            self.carry = max(0.0, self.remaining(self.step))
        self.step = step
        self.step_started = self.clock()

    def allowance(self, step: str) -> float:
        return self.shares[step] * self.ceiling + self.carry

    def remaining(self, step: str) -> float:
        """Seconds this step may still use: its allowance, capped by the ceiling."""
        now = self.clock()
        in_step = now - self.step_started
        total_left = self.ceiling - (now - self.t0)
        return min(self.allowance(step) - in_step, total_left)

    def can_afford(self, step: str, seconds: float) -> bool:
        return self.remaining(step) >= seconds

    def pool_left(self) -> float:
        """The `ladders` share not yet drawn, capped by the ceiling: what pays a
        rung its own step can no longer pay for (finding 55)."""
        total_left = self.ceiling - (self.clock() - self.t0)
        return min(self.shares.get("ladders", 0.0) * self.ceiling - self.pool_drawn, total_left)

    def draw(self, seconds: float) -> None:
        self.pool_drawn += seconds


def spent_before(home) -> float:
    """Seconds this episode's earlier runs logged (timing.jsonl), 0.0 when
    there is none yet.  What `Budget.charge` is charged with at context
    creation, so the ceiling binds across resumes."""
    import json
    from pathlib import Path
    path = Path(home) / "timing.jsonl"
    if not path.exists():
        return 0.0
    total = 0.0
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                total += float(json.loads(line).get("seconds") or 0.0)
            except (ValueError, TypeError):
                continue
    return total
