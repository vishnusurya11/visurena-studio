"""The downstream reserve (C3_p90_residual §4, ruled 2026-10-11 for the owner,
for veto): a rung runs only if the episode's spent clock + its price + the
shares of the firsts still owed after its step fit under the owner's 6 h.

The 5 h ceiling bounds rungs, never firsts, so it cannot bound an episode whose
crossing lands before its firsts are done: ep21 crossed 20 min into step 09's
32-take round 0 and could not end before 6.3 h.  A refusal is the ceiling's
terminal (D3): a ladder signs its best, flagged; the plan follows its tags.
Nothing parks; firsts are never refused; an unpriced rung costs nothing."""
from __future__ import annotations

import pytest

from studio import judged_gate, plan_verdict
from studio.ladder import Rung
from studio.run_budget import EPISODE_SHARES, OWNER_LIMIT_SECONDS, Budget
from tests.test_step_02_plan import conn, ctx  # noqa: F401 -- the step-02 fixtures

H = 3600.0


def budget(spent: float, step: str, limit: float | None = OWNER_LIMIT_SECONDS) -> Budget:
    b = Budget(18000, EPISODE_SHARES, clock=lambda: 0.0, limit=limit)
    b.charge(spent)
    b.start(step)
    return b


class Ctx:
    def __init__(self, b: Budget):
        self.budget, self.learned = b, []

    def learn(self, learning):
        self.learned.append(learning)


def test_the_firsts_owed_are_the_shares_of_the_steps_after():
    b = budget(0.0, "02")
    assert round(b.owed_after("02") / 60) == 203        # 03 .. 13 of the 300-min table
    assert round(b.owed_after("08") / 60) == 137
    assert round(b.owed_after("09") / 60) == 32
    assert b.owed_after("13") == 0.0 and b.owed_after("judges") == 0.0
    assert OWNER_LIMIT_SECONDS == 6 * H


def test_a_rung_runs_only_while_the_firsts_still_fit_under_six_hours():
    assert budget(2 * H, "08").leaves_reserve("08", 300.0)          # 120 + 5 + 137 = 262 min
    assert not budget(4 * H, "08").leaves_reserve("08", 300.0)      # 240 + 5 + 137 = 382 min
    assert budget(4 * H, "08").leaves_reserve("08", 0.0)            # an unpriced rung spends nothing
    assert budget(4 * H, "08", limit=None).leaves_reserve("08", 300.0)   # no limit: the trailer, sheets


def test_affordable_refuses_on_the_reserve_and_closes_the_rungs():
    poor = Ctx(budget(4 * H, "08"))                                 # an hour of 5 h headroom left
    assert judged_gate.affordable(poor, "EYE_PANELS", Rung("reprose", 300.0), taken=1) is False
    assert poor.learned[-1].gate == "budget" and poor.learned[-1].action == "reserve"
    assert poor.budget.rungs_closed() and not poor.budget.ceiling_spent()
    rich = Ctx(budget(2 * H, "08"))
    assert judged_gate.affordable(rich, "EYE_PANELS", Rung("reprose", 300.0), taken=1) is True
    assert not rich.budget.rungs_closed()


def _three_hours(ctx):
    ctx.open_step("02")                         # as step_runner does before the step
    ctx.budget.charge(3 * H)                    # 180 + 4 + 203 > 360: no priced plan rung fits


def test_a_reserve_refused_plan_signs_its_judged_best_flagged_and_never_defers(ctx, monkeypatch):
    from scripts.episode import step_02_plan as step
    from tests.test_a_killed_plan_climb_resumes_from_its_best_draft import LINES, Writer, _wire
    LINES["J"] = ["G-CROWD shot 2: six walk-ons"]
    _three_hours(ctx)
    _wire(ctx, monkeypatch, Writer(*["J"] * 8))
    step.run(ctx)
    doc = plan_verdict.read(step.plan_of(ctx))
    assert doc["flagged"] is True and not (ctx.home / "plan.deferred.json").exists()
    assert not ctx.budget.ceiling_spent()


def test_a_reserve_refused_builder_line_climbs_at_most_three_then_stops(ctx, monkeypatch):
    from scripts.episode import step_02_plan as step
    from tests.test_a_killed_plan_climb_resumes_from_its_best_draft import LINES, Writer, _wire
    LINES["K"] = ["G-TAKELINT   : 1", "    G-TAKELINT shot 9: 'slowly' [plan]"]
    _three_hours(ctx)
    writer = Writer(*["K"] * 12)
    _wire(ctx, monkeypatch, writer)
    with pytest.raises(SystemExit, match="SAFETY: plan_builder"):
        step.run(ctx)
    assert len(writer.previous) <= 1 + 3


def test_the_episode_context_carries_the_owner_limit(ctx):
    assert ctx.budget.limit == OWNER_LIMIT_SECONDS
