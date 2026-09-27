"""A take rung its step cannot pay for is paid by the ladders' pool, never
skipped in silence.

ep13 (2026-09-27): after move_type the 09 share was spent; `take_ladder.
can_afford` asked the step share alone and RETURNED -- no retake, no defer, no
line in the log -- so shorter_take, the one cure for T11's +1.08 s lip-sync
lag, ran for 0 s and the ladder signed keep_best over it.
"""
from studio import take_ladder
from studio.run_budget import Budget


class Ctx:
    def __init__(self, t):
        self.budget = Budget(10_000, {"09": 0.1, "ladders": 0.3}, clock=lambda: t[0])
        self.budget.start("09")


def test_the_pool_pays_a_take_rung_the_step_cannot():
    t = [0.0]
    ctx = Ctx(t)
    t[0] = 1500.0                                   # 09's 1000 s share spent
    assert take_ladder.can_afford(ctx, take_ladder.SHORTER_TAKE, 1)


def test_a_dry_pool_is_said_not_swallowed():
    import pytest
    t = [0.0]
    ctx = Ctx(t)
    t[0] = 9_990.0                                  # 10 s under the ceiling
    with pytest.raises(SystemExit, match="DEFERRED"):
        take_ladder.can_afford(ctx, take_ladder.SHORTER_TAKE, 1)
