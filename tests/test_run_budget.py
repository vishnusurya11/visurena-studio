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


class TestEpisodeSharesAgainstTheCapTable:
    """P12 #8: the shares are rung prices under the 5 h ceiling, the cap table is first-pass wall
    under 6 h.  Checked on master before calling step 07 a bug: 07 is 22 min of a 30 min wall."""

    # Steps whose share x ceiling is ABOVE their summed wall at HEAD: no cap value moved (P12);
    # the owner sees them in the report.  A fix empties this set and the test says so.
    SHARE_ABOVE_WALL = {"02", "12"}

    def test_the_episode_shares_sum_to_one(self):
        from studio.run_budget import EPISODE_SHARES
        assert abs(sum(EPISODE_SHARES.values()) - 1.0) < 1e-9

    def test_each_share_times_the_ceiling_fits_its_steps_wall(self):
        from studio import step_caps
        from studio.run_budget import EPISODE_CEILING_SECONDS, EPISODE_SHARES
        over = {s for s, share in EPISODE_SHARES.items() if s.isdigit()
                and share * EPISODE_CEILING_SECONDS > step_caps.step_wall_s(s) + 1e-6}
        assert over == self.SHARE_ABOVE_WALL


class TestTheDarkBudgetLog:
    """P12 #9: budget.jsonl records what the budget WOULD cut; nothing is cut until 2 dark episodes."""

    def test_deadline_subtracts_the_measured_granularity(self):
        b = make(ceiling=1000.0)
        b.start("a")
        assert b.deadline("a", granularity=0.0) == 500.0
        assert b.deadline("a", granularity=120.0) == 380.0

    def test_a_dark_row_says_would_cut_and_is_appended(self, tmp_path):
        from studio.run_budget import append_dark, dark_row, read_dark
        b = make(ceiling=1000.0)
        b.start("a")
        append_dark(tmp_path, dark_row(b, "a", 600.0))
        append_dark(tmp_path, dark_row(b, "a", 100.0))
        rows = read_dark(tmp_path)
        assert [r["would_cut"] for r in rows] == [True, False] and rows[0]["step"] == "a"

    def test_no_cut_before_two_dark_episodes(self):
        from studio.run_budget import cuts_allowed
        assert [cuts_allowed(n) for n in (0, 1, 2, 3)] == [False, False, True, True]
