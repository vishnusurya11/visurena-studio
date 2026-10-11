"""C3_verdict #6 (D10): the plan rungs are priced at their measured medians
(improve 240 s, model_tier 90 s) and EPISODE_SHARES take C3_T §3.3's table.

The old shares were fiction against stage_p90.json (02 had 8 of 300 min and
spent 45-64 at P50; 09 had 120 and needs ~98 with CK8).  Below the ceiling the
change is behaviour-neutral -- headroom pays a rung its share cannot (1 budget
terminal in 9 episodes) -- and at a spent clock the plan ladder now goes
terminal instead of climbing for free."""
from __future__ import annotations

import math

from studio import plan_ladder
from studio.run_budget import EPISODE_CEILING_SECONDS, EPISODE_SHARES

T3_3 = {"01": 1, "02": 70, "03": 5, "04": 15, "05": 1, "06": 1, "07": 22, "08": 22, "09": 105, "10": 6,
        "11": 20, "12": 3, "13": 3, "judges": 6, "ladders": 20, "slack": 0}


def test_the_shares_are_c3_t_table_and_sum_to_one():
    assert math.isclose(sum(EPISODE_SHARES.values()), 1.0)
    assert {k: round(v * 300) for k, v in EPISODE_SHARES.items()} == T3_3
    assert EPISODE_CEILING_SECONDS == 5 * 3600                  # D5: the ceiling stays 5 h


def test_the_plan_rungs_cost_their_measured_medians():
    rungs = {r.name: r.cost_seconds for r in plan_ladder.ladder().rungs}
    assert rungs == {"improve": 240.0, "model_tier": 90.0}
    assert [r.cost_seconds for r in plan_ladder.ladder_over_clock().rungs] == [0.0, 0.0]
    assert [r.cost_seconds for r in plan_ladder.ladder_after(1).rungs] == [240.0, 90.0]


def test_below_the_ceiling_every_plan_rung_is_affordable():
    from studio import judged_gate
    from tests.test_the_clock_covers_the_whole_episode import Ctx
    ctx = Ctx(spent=4 * 3600)                                   # 4 h in: an hour of headroom
    ctx.budget.start("02")
    for rung in plan_ladder.ladder().rungs:
        assert judged_gate.affordable(ctx, "PLAN", rung, taken=0)


def test_a_spent_clock_takes_no_priced_plan_rung():
    from studio import judged_gate
    from tests.test_the_clock_covers_the_whole_episode import Ctx
    ctx = Ctx(spent=EPISODE_CEILING_SECONDS + 1)
    ctx.budget.start("02")
    assert not judged_gate.affordable(ctx, "PLAN", plan_ladder.ladder().rungs[0], taken=0)
