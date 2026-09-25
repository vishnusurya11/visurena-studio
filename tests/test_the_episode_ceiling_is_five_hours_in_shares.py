"""The episode's render approval is a wall-clock ceiling: 18 000 s (five hours)
against today's 3.5-4 h, shared out by step id the way the trailer's is, with
the judges and the ladders holding shares of their own."""
from __future__ import annotations

from studio import registry
from studio.run_budget import EPISODE_CEILING_SECONDS, EPISODE_SHARES, Budget


def test_the_ceiling_is_five_hours():
    assert EPISODE_CEILING_SECONDS == 5 * 3600 == 18000


def test_the_shares_sum_to_one():
    assert abs(sum(EPISODE_SHARES.values()) - 1.0) < 1e-9


def test_every_episode_step_holds_a_share_and_so_do_the_judges_and_ladders():
    ids = {entry["id"] for entry in registry.steps("episode")}
    assert ids <= set(EPISODE_SHARES)
    assert {"judges", "ladders", "slack"} <= set(EPISODE_SHARES)


def test_a_budget_opens_on_the_shares():
    budget = Budget(EPISODE_CEILING_SECONDS, EPISODE_SHARES, clock=lambda: 0.0)
    budget.start("09")
    assert budget.remaining("09") == EPISODE_SHARES["09"] * EPISODE_CEILING_SECONDS
    assert budget.can_afford("09", 7200)
