"""A sha gap in the cure ledger -- a hand edit nobody recorded -- never
re-signs: `resigned` answers False, nothing is signed, and the plan takes the
ordinary climb, where a clean battery costs exactly one critic read."""
from __future__ import annotations

import json

from studio import episode_home, plan_provenance, plan_verdict

from tests.test_a_mechanically_cured_plan_is_resigned_without_the_critic import Ctx, no_paid_calls  # noqa: F401
from scripts.episode import step_02_plan as step


def test_a_sha_gap_returns_false_and_signs_nothing(tmp_path, no_paid_calls):  # noqa: F811
    plan = episode_home.plan_path(tmp_path / "book", 3)
    plan.parent.mkdir(parents=True)
    plan.write_text(json.dumps({"v": 1}), encoding="utf-8")
    plan_verdict.sign(plan, "signed clean", signed_by="judge:plan@1")
    before = plan_verdict.plan_sha8(plan)
    plan.write_text(json.dumps({"v": 2}), encoding="utf-8")
    plan_provenance.record(plan, before, ["holds"])
    plan.write_text(json.dumps({"v": "hand edited"}), encoding="utf-8")   # no recorded row
    ctx = Ctx(tmp_path, rc=0)
    assert step.resigned(ctx) is False
    assert plan_verdict.current(plan) is False
    assert ctx.captured == []               # the chain broke before the battery was even asked
