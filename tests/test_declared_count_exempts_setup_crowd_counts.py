"""G-CROWD asks `extras >= 1` on a wide over a crowd setup; the writer obeyed with the setup's own count
(extras=2, 3) and the critic refused it as "invented: count extras=2 has no chapter span" because
`declared_count` exempted only == 1 (Jekyll ep01 Kawajiri, 2026-10-18).  Fix the judge, not the writer.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from studio.episode_spec import Episode  # noqa: E402
from studio.judges import plan as plan_judge  # noqa: E402
from studio.judges.plan import Answer, Claim, PlanReading, Turn  # noqa: E402

FIX = Path(__file__).parent / "fixtures" / "ep01_replay" / "P01"


def ep01() -> Episode:
    return Episode.model_validate(json.loads((FIX / "plan.json").read_text(encoding="utf-8")))


def reading(*claims: Claim) -> PlanReading:
    return PlanReading(turn=Turn(), answer=Answer(), claims=list(claims))


def count(shot: int, n: int) -> Claim:
    return Claim(shot=shot, kind="count", claim=f"extras={n}", span="")


def test_shots_one_and_eighteen_over_a_crowd_setup_give_no_invented_fault():
    plan = ep01()
    claims = [count(1, 2), count(18, 3)]
    assert all(plan_judge.declared_count(plan, c) for c in claims)
    assert plan_judge.claim_faults(plan, [reading(*claims)], "a chapter that never says two") == []


def test_extras_on_a_setup_with_no_crowd_still_fault():
    plan = ep01()
    bare = next(s for s in plan.shots if not (plan.setups[s.setup].crowd or "").strip())
    claim = count(bare.index, 2)
    assert plan_judge.declared_count(plan, claim) is False
    faults = plan_judge.claim_faults(plan, [reading(claim)], "nothing")
    assert [f.kind for f in faults] == ["invented"]


def test_extras_zero_and_other_kinds_are_not_declared():
    plan = ep01()
    assert plan_judge.declared_count(plan, count(1, 0)) is False
    assert plan_judge.declared_count(plan, Claim(shot=1, kind="prop", claim="extras=2")) is False
