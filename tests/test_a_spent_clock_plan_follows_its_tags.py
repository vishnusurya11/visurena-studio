"""C3_verdict #5 (iv), D3: the plan at a spent clock follows its battery tags.

"Ship the best plan at the ceiling" crashes at step 06/09 when the best plan
carries a line a downstream builder refuses anyway (takes_r2v.opened repeats
G-LIGHT, PLAN GATES, TAKE LENGTH; seq_boards repeats CAST BOUND and ACTOR;
step 06 the take lint).  So: a best draft with only JUDGED lines signs
keep_best, flagged; one with a BUILDER line climbs once more over the clock
(at most 3 rungs) and, still carrying one, stops as a SAFETY refusal."""
from __future__ import annotations

import pytest

from scripts.episode import step_02_plan as step
from studio import plan_verdict
from tests.test_a_killed_plan_climb_resumes_from_its_best_draft import LINES, Writer, _wire
from tests.test_step_02_plan import conn, ctx  # noqa: F401


def _spend(ctx):
    ctx.budget.charge(ctx.budget.ceiling + 1)


def test_a_judged_only_best_draft_signs_keep_best_flagged(ctx, monkeypatch):
    LINES["J"] = ["G-CROWD shot 2: six walk-ons"]
    _spend(ctx)
    _wire(ctx, monkeypatch, Writer(*["J"] * 8))
    step.run(ctx)
    plan = step.plan_of(ctx)
    doc = plan_verdict.read(plan)
    assert plan_verdict.current(plan) and doc["flagged"] is True
    assert not (ctx.home / "plan.deferred.json").exists()


def test_a_builder_line_climbs_at_most_three_rungs_then_stops(ctx, monkeypatch):
    LINES["K"] = ["G-TAKELINT   : 1", "    G-TAKELINT shot 9: 'slowly' [plan]"]
    _spend(ctx)
    writer = Writer(*["K"] * 12)
    _wire(ctx, monkeypatch, writer)
    with pytest.raises(SystemExit, match="SAFETY: plan_builder"):
        step.run(ctx)
    assert len(writer.previous) <= 1 + 3 + 3       # round 0, the ladder (free until priced), <= 3 over the clock
    assert not plan_verdict.current(step.plan_of(ctx))


def test_below_the_ceiling_a_battery_refusal_still_defers(ctx, monkeypatch):
    from studio.deferral import Deferred
    LINES["J"] = ["G-CROWD shot 2: six walk-ons"]
    _wire(ctx, monkeypatch, Writer(*["J"] * 8))
    with pytest.raises(Deferred):
        step.run(ctx)
