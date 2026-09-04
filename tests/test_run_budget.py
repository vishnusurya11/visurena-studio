"""The time ceiling every unattended trailer run lives under.

Nothing in the trailer chain spends money, so the only budget is wall-clock.
A step reads its remaining share before every render; when it cannot afford
the next rung of its ladder it takes the terminal rung instead of asking.
"""
from studio.run_budget import Budget, TRAILER_SHARES


class FakeClock:
    def __init__(self, t: float = 0.0):
        self.t = t

    def __call__(self) -> float:
        return self.t


def make(ceiling=3600.0, shares=None, clock=None):
    return Budget(ceiling_seconds=ceiling, shares=shares or {"a": 0.5, "b": 0.5},
                  clock=clock or FakeClock())


class TestShares:
    def test_trailer_shares_sum_to_one_including_slack(self):
        assert abs(sum(TRAILER_SHARES.values()) - 1.0) < 1e-9

    def test_a_step_starts_with_its_share_of_the_ceiling(self):
        b = make()
        b.start("a")
        assert b.remaining("a") == 1800.0

    def test_elapsed_time_in_a_step_is_charged_to_it(self):
        clock = FakeClock()
        b = make(clock=clock)
        b.start("a")
        clock.t = 600.0
        assert b.remaining("a") == 1200.0


class TestRollForward:
    def test_unused_share_rolls_into_the_next_step(self):
        clock = FakeClock()
        b = make(clock=clock)
        b.start("a")
        clock.t = 300.0           # used 300 of 1800
        b.start("b")
        assert b.remaining("b") == 1800.0 + 1500.0

    def test_overrun_is_taken_from_the_next_step(self):
        clock = FakeClock()
        b = make(clock=clock)
        b.start("a")
        clock.t = 2400.0          # 600 over
        b.start("b")
        assert b.remaining("b") == 1200.0

    def test_the_ceiling_binds_regardless_of_shares(self):
        clock = FakeClock()
        b = make(ceiling=1000.0, shares={"a": 0.1, "b": 0.9}, clock=clock)
        b.start("a")
        clock.t = 950.0
        b.start("b")
        assert b.remaining("b") == 50.0


class TestAfford:
    def test_can_afford_within_share(self):
        b = make()
        b.start("a")
        assert b.can_afford("a", 1799.0)

    def test_cannot_afford_past_share(self):
        b = make()
        b.start("a")
        assert not b.can_afford("a", 1801.0)

    def test_unknown_step_is_a_bug_not_a_zero(self):
        b = make()
        try:
            b.start("zzz")
        except KeyError:
            return
        raise AssertionError("unknown step must raise")
