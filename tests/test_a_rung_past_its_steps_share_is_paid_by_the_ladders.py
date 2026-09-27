"""A rung past its step's share is paid from the ladders' own pool.

ep13 run w (2026-09-27, finding 55): the 125-min 09 share held the render, both
checkers and nothing else; EYE_TAKES deferred before its first retake with
-1304 s, while the 50-min `ladders` share -- priced for exactly this -- sat
unspent.  The pool is drawn at each rung's price; dry, the run still defers,
and the ceiling still binds last.
"""
import pytest

from studio import judged_gate
from studio.ladder import Rung
from studio.run_budget import Budget

SHARES = {"09": 0.1, "ladders": 0.1}


class Ctx:
    def __init__(self, t):
        self.stage, self.unit = "episode", "ep13"
        self.budget = Budget(10_000, SHARES, clock=lambda: t[0])
        self.learned = []

    def learn(self, learning):
        self.learned.append(learning)


def test_the_pool_pays_when_the_step_cannot():
    t = [0.0]
    ctx = Ctx(t)
    ctx.budget.start("09")
    t[0] = 1500.0                                   # 09's 1000 s share overrun by 500 s
    assert judged_gate.affordable(ctx, "EYE_TAKES", Rung("seed", 600.0), 0)
    assert ctx.budget.pool_left() == 400.0


def test_a_dry_pool_still_defers():
    t = [0.0]
    ctx = Ctx(t)
    ctx.budget.start("09")
    t[0] = 1500.0
    judged_gate.affordable(ctx, "EYE_TAKES", Rung("seed", 600.0), 0)
    with pytest.raises(SystemExit, match="DEFERRED"):
        judged_gate.affordable(ctx, "EYE_TAKES", Rung("seed", 600.0), 1)


def test_the_ceiling_still_binds_the_pool():
    t = [0.0]
    ctx = Ctx(t)
    ctx.budget.start("09")
    t[0] = 9_800.0                                  # 200 s left under the ceiling
    assert ctx.budget.pool_left() == 200.0
