"""The time ceiling of an unattended trailer run.

Nothing in the trailer chain spends money -- MiniMax Music 3, MiniMax-H3 and
Qwen3-TTS all run on the local ComfyUI -- so the one budget is wall-clock.
Each step owns a SHARE of the ceiling; unused time rolls forward, overruns
are charged forward, and the ceiling itself binds last.  A step asks
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
    "01": 3 / 300, "02": 8 / 300, "03": 12 / 300, "04": 12 / 300, "05": 2 / 300,
    "06": 3 / 300, "07": 4 / 300, "08": 20 / 300, "09": 135 / 300, "10": 8 / 300,
    "11": 8 / 300, "12": 2 / 300,
    "judges": 15 / 300, "ladders": 60 / 300, "slack": 8 / 300,
}
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
        self.carry = 0.0          # unused (+) or overrun (-) from earlier steps

    def start(self, step: str) -> None:
        """Close the running step, carry its balance, open `step`."""
        if step not in self.shares:
            raise KeyError(f"no time share for step {step!r}")
        if self.step is not None:
            self.carry = self.remaining(self.step)
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
