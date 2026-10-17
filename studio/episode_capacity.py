"""How many shots an episode can hold inside the owner's 6 h (anime-TV grammar).

Every cut shot is one take (`episode_takes.budget_for`: a grammar plan never
packs two shots into one take), one grid cell, one panel read and one take
check, so the episode's machine time grows with its shot count.  The model reads
the budget the runner itself runs on -- `run_budget.EPISODE_SHARES`, priced on
WotW ep25's 26 shots (C3_T section 3.3, the clean run) -- splitting the steps
that scale per shot (grids, panels, takes, judges, the ladders' pool) from the
ones that do not (plan, places, lines, timeline, edit, QC, deliver, publish), and
adds a retake margin from the H3 numbers (03_h3_workflows.md section 1: a render
is ~110 s; a quarter of the takes retaken twice).  CHECK: at 23 shots it
projects 5.0 h, and Jekyll ep01's clock measured 4.99 h.
"""
from __future__ import annotations

import math

from studio.run_budget import EPISODE_CEILING_SECONDS, EPISODE_SHARES, OWNER_LIMIT_SECONDS
from studio.plan_gates import fault

PER_SHOT_STEPS = ("07", "08", "09", "judges", "ladders")
"""The shares that scale with the shot count."""
PRICED_SHOTS = 26
"""The shots of the run the shares were priced on (WotW ep25)."""
RENDER_S = 110.0
"""One H3 render, whole prompt (03 section 1: median of 138 renders 111 s)."""
RETAKE_MINUTES = 0.25 * 2 * RENDER_S / 60
"""Per shot: a quarter of the takes retaken twice."""


def per_shot_minutes() -> float:
    """Machine minutes one more shot costs."""
    priced = sum(EPISODE_SHARES[k] for k in PER_SHOT_STEPS) * EPISODE_CEILING_SECONDS / 60
    return priced / PRICED_SHOTS + RETAKE_MINUTES


def fixed_minutes() -> float:
    """Machine minutes an episode costs whatever its shot count."""
    whole = sum(EPISODE_SHARES.values()) * EPISODE_CEILING_SECONDS / 60
    return whole - sum(EPISODE_SHARES[k] for k in PER_SHOT_STEPS) * EPISODE_CEILING_SECONDS / 60


def projected_hours(shots: int) -> float:
    return (fixed_minutes() + per_shot_minutes() * shots) / 60


def max_shots() -> int:
    """The most shots whose projection fits the owner's limit."""
    return math.floor((OWNER_LIMIT_SECONDS / 60 - fixed_minutes()) / per_shot_minutes())


MAX_SHOTS = min(max_shots(), 28)
"""The cap: 28 (5.65 h), not the 30 that fit (5.91 h).  Main session 2026-10-17, for the
owner's veto: 30 leaves ~5 min of the 6 h, and the shares that price the downstream
reserve (`Budget.owed_after`) still assume ~26 shots.  Re-price after the first grammar
episode's measured clock, then revisit."""


def shot_faults(episode) -> list[str]:
    """G-SHOTS: the cut holds at most MAX_SHOTS shots."""
    omit = set(getattr(episode, "omit", None) or [])
    got = sum(1 for s in episode.shots if s.index not in omit)
    if got <= MAX_SHOTS:
        return []
    return [fault("G-SHOTS", "plan", f"shots in the cut -- {projected_hours(got):.1f} h projected against "
                  f"the owner's {OWNER_LIMIT_SECONDS // 3600} h", got, MAX_SHOTS)]
