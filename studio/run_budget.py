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
    "01": 1 / 300, "02": 70 / 300, "03": 5 / 300, "04": 15 / 300, "05": 1 / 300,
    "06": 1 / 300, "07": 22 / 300, "08": 22 / 300, "09": 105 / 300, "10": 6 / 300,
    "11": 20 / 300, "12": 3 / 300, "13": 3 / 300,
    "judges": 6 / 300, "ladders": 20 / 300, "slack": 0 / 300,
}
# RE-PRICED 2026-10-11 (C3_verdict #6, D10) on C3_T §3.3's measured relaunch-free
# values (stage_p90.json, ep25 the clean run): 02 plan 70 (P50 45-64 after
# fresh_brief), 07 grids 22, 08 panels 22, 09 takes 105 (P50 118 x CK8's 0.83),
# 11 QC + master eye 20, the ladders' pool 20.  Below the ceiling nothing changes
# (headroom pays a rung its share cannot: 1 budget terminal in 9 episodes).
# 2026-10-06: 13 (publish: upload + the /shorts/ poll, capped 600 s) takes 5 min from
# 09, whose measured need (ep13: 7176 s) fits 120.
# RE-PRICED 2026-09-27 from ep13's clock: step 08 spent ~15 min on the content read
# and ~13 min on the judge's reads per pass -- 28 min of a 20-min share, so every run
# deferred before one redraw rung.  08 now holds its reads plus one full rung; the
# takes keep 125 min (ep13 asked 7176 s); places and lines are mostly cached (6 each).
"""Minutes of the 300, as fractions, keyed by episode step id; the judges
(capped at 15 GPU min) and the ladders (60 min: panels 10, takes 40, master
retake 10) hold shares of their own.  Unused time rolls forward."""


OWNER_LIMIT_SECONDS = 6 * 3600
"""The owner's rule (2026-10-11): 6 h for EVERY episode, zero input.  The 5 h
ceiling bounds rungs, never firsts, so a crossing before the firsts are done
ends late (ep21: 20 min into round 0, 6.3 h floor).  The downstream reserve
measures each rung against this limit less the firsts still owed."""


CHEAP_CHECK_SECONDS = 60.0
"""A check this cheap always runs, whatever the clock: a minute cannot save an episode."""


class Budget:
    """Wall-clock shares per step, rolling forward, under one ceiling; with a
    `limit`, a rung must also leave the firsts after its step their shares."""

    def __init__(self, ceiling_seconds: float, shares: dict[str, float],
                 clock: Callable[[], float] = time.monotonic, limit: float | None = None):
        self.ceiling = ceiling_seconds
        self.shares = shares
        self.clock = clock
        self.limit = limit
        self.t0 = clock()
        self.step: str | None = None
        self.step_started = self.t0
        self.carry = 0.0          # unused time from earlier steps
        self.pool_drawn = 0.0     # the `ladders` share drawn by rungs
        self.reserve_hit = False  # a rung was refused to keep the firsts' time

    def owed_after(self, step: str) -> float:
        """Seconds the firsts after `step` are priced at: the shares of the
        numbered steps that follow it (the judges' and ladders' pools are not
        firsts).  0.0 for the last step or a pool."""
        steps = sorted(s for s in self.shares if s.isdigit())
        if step not in steps:
            return 0.0
        return sum(self.shares[s] for s in steps[steps.index(step) + 1:]) * self.ceiling

    def leaves_reserve(self, step: str, seconds: float) -> bool:
        """Whether a rung of `seconds` still leaves the firsts owed after `step`
        their time under the owner's limit.  No limit, or an unpriced rung: yes."""
        if self.limit is None or seconds <= 0:
            return True
        return (self.clock() - self.t0) + seconds + self.owed_after(step) <= self.limit

    def checks_cut(self, step: str, seconds: float) -> bool:
        """Whether a CHECK (a measure or a re-measure, never a re-render) of
        `seconds` must be cut for time.  A check is cut only when running it
        would eat the reserve the firsts after `step` need under the owner's
        limit; a cheap one never is.  The 5 h ceiling closes rungs, not checks
        (owner 2026-10-14, Jekyll HEL ep01).  With no limit, the ceiling rule."""
        if seconds <= CHEAP_CHECK_SECONDS:
            return False
        if self.limit is None:
            return self.ceiling_spent()
        return not self.leaves_reserve(step, seconds)

    def rungs_closed(self) -> bool:
        """No more rescue rungs this run: the ceiling is spent, or the reserve
        refused one.  Either way a ladder's terminal is the ceiling's (D3)."""
        return self.ceiling_spent() or self.reserve_hit

    def charge(self, spent: float) -> None:
        """Seconds earlier RUNS of this episode already spent (timing.jsonl):
        the ceiling covers the episode, not the process.  ep14's 31 driver
        runs each opened a fresh 5 h (five-hour plan fix 1, 2026-09-30)."""
        self.t0 -= max(0.0, spent)

    def ceiling_spent(self) -> bool:
        """The episode's whole ceiling is gone: no rung can ever be paid for
        again, so a refusal here is TERMINAL, never a deferral."""
        return self.clock() - self.t0 >= self.ceiling

    def headroom(self) -> float:
        """Seconds the episode's ceiling has left.  Shares are an ALLOCATION
        of the ceiling, so headroom pays what an exhausted share cannot
        (ep16: an empty 09 share deferred 'run again to resume' forever while
        the clock sat at 4.6 of 5 h -- idling clocks nothing, so that money
        could never appear)."""
        return max(0.0, self.ceiling - (self.clock() - self.t0))

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

    def deadline(self, step: str, granularity: float = 0.0) -> float:
        """The clock reading at which `step` should stop starting calls: what it may still use,
        less the longest call in flight that is never cut (the measured granularity)."""
        return self.clock() + max(0.0, self.remaining(step) - granularity)

    def can_afford(self, step: str, seconds: float) -> bool:
        return self.remaining(step) >= seconds

    def pool_left(self) -> float:
        """The `ladders` share not yet drawn, capped by the ceiling: what pays a
        rung its own step can no longer pay for (finding 55)."""
        total_left = self.ceiling - (self.clock() - self.t0)
        return min(self.shares.get("ladders", 0.0) * self.ceiling - self.pool_drawn, total_left)

    def draw(self, seconds: float) -> None:
        self.pool_drawn += seconds


CLOCK_RESET = "clock_reset.json"
"""The owner's `retry` stamps an ATTEMPT here (C3_verdict #4, D2): for the
audit and for the ladders' own round counters (a retry's fresh take rounds,
a keep_best signed before it re-judged).  The ceiling NEVER reads it: 67
retries each opened a fresh 5 h before (ep19-27), so the 6 h was unmeasurable."""


def stamp_attempt(home, at: str | None = None) -> str:
    """Stamp the home with this attempt's start (local ISO, the timing rows'
    own convention), now by default.  Returns the stamp."""
    import json
    from datetime import datetime
    from pathlib import Path
    stamp = at or datetime.now().isoformat(timespec="seconds")
    Path(home).mkdir(parents=True, exist_ok=True)
    (Path(home) / CLOCK_RESET).write_text(json.dumps({"attempt_at": stamp}), encoding="utf-8")
    return stamp


def clock_reset_at(home) -> str:
    """The attempt stamp (a legacy file's `at` too), or ""."""
    import json
    from pathlib import Path
    path = Path(home) / CLOCK_RESET
    try:
        doc = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        return str(doc.get("attempt_at") or doc.get("at") or "")
    except (ValueError, OSError, AttributeError):
        return ""


def clock_reset_epoch(home) -> float:
    """The stamp as seconds since the epoch (local, as it was written); 0.0 when none."""
    from datetime import datetime
    stamp = clock_reset_at(home)
    try:
        return datetime.fromisoformat(stamp).timestamp() if stamp else 0.0
    except ValueError:
        return 0.0


def spent_before(home) -> float:
    """Seconds this episode already spent, from its first launch, 0.0 when none
    yet: the union of its run spans (studio.run_clock, C3_verdict #3 -- a
    killed run counts to its last beat) plus legacy timing.jsonl rows from
    before the first run row.  No retry resets it (C3_verdict #4).  What
    `Budget.charge` is charged with at context creation."""
    from studio import run_clock
    return run_clock.spent(home)


DARK_EPISODES_REQUIRED = 2
"""The budget only watches (writes `would_cut`) until this many episodes ran dark (P12, owner 2026-10-19)."""
DARK_LOG = "budget.jsonl"


def cuts_allowed(dark_episodes: int) -> bool:
    return dark_episodes >= DARK_EPISODES_REQUIRED


def dark_row(budget: "Budget", step: str, seconds: float) -> dict:
    """What the budget would have said of a call of `seconds`: nothing is cut by it."""
    return {"step": step, "seconds": round(seconds, 1), "remaining": round(budget.remaining(step), 1),
            "would_cut": not budget.can_afford(step, seconds)}


def append_dark(home, row: dict) -> None:
    import json
    from pathlib import Path
    path = Path(home) / DARK_LOG
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")


def read_dark(home) -> list[dict]:
    import json
    from pathlib import Path
    path = Path(home) / DARK_LOG
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    return [json.loads(l) for l in lines if l.strip()]
