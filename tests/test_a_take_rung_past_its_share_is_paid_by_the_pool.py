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


def test_headroom_pays_a_dry_pool_and_true_exhaustion_is_a_no():
    """The deferral is gone (ep16 fix, then the five-hour verdict): a dry
    share and pool are paid by the episode's remaining headroom; when even
    the headroom cannot pay, can_afford answers False -- the ladder's
    terminal rung acts on it in the same run, never 'run again to resume'."""
    t = [0.0]
    ctx = Ctx(t)
    t[0] = 9_990.0                                  # 10 s under the ceiling
    assert take_ladder.can_afford(ctx, take_ladder.SHORTER_TAKE, 1) is False
    t[0] = 5_000.0                                  # dry share and pool would overdraw, headroom pays
    ctx2 = Ctx(t)
    ctx2.budget.draw(3_000.0)                       # the pool spent
    t[0] = 6_500.0
    assert take_ladder.can_afford(ctx2, take_ladder.SHORTER_TAKE, 1) is True
