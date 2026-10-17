"""The shot cap (anime-TV grammar, 2026-10-17): shorter shots mean more of them
(about 28-32), and every shot is a take, a grid cell, a panel read and a take
check.  The owner's limit is 6 h of machine work an episode, zero input.

The model reads the budget the code runs on (`run_budget.EPISODE_SHARES`, priced
on WotW ep25's 26 shots, C3_T section 3.3) plus a retake margin from the H3
numbers (03_h3_workflows.md: a render ~110 s; a quarter of the takes retaken
twice).  At 23 shots it projects 5.0 h -- Jekyll ep01's measured clock (4.99 h).
The cap is the largest count that fits 6 h: 30.  $0."""
from __future__ import annotations

from types import SimpleNamespace

from studio import episode_capacity as cap


def test_the_per_shot_and_fixed_minutes_come_from_the_shares():
    assert round(cap.per_shot_minutes(), 2) == round(175 / 26 + cap.RETAKE_MINUTES, 2)
    assert round(cap.fixed_minutes()) == 125


def test_23_shots_project_jekyll_ep01s_five_hours():
    assert 4.8 <= cap.projected_hours(23) <= 5.2


def test_thirty_shots_is_the_most_that_fit_six_hours():
    assert cap.max_shots() == 30
    assert cap.projected_hours(30) <= 6.0 < cap.projected_hours(31)


def test_the_cap_is_28_until_the_retake_shares_are_repriced():
    """Main session 2026-10-17, for the owner's veto: 30 fits with ~5 min to spare and the
    shares that price the reserve still assume ~26 shots, so the cap is 28 (5.65 h)."""
    assert cap.MAX_SHOTS == 28 and cap.projected_hours(28) <= 5.7


def test_a_plan_past_the_cap_is_refused_and_one_at_it_is_not():
    shots = [SimpleNamespace(index=i) for i in range(29)]
    got = cap.shot_faults(SimpleNamespace(shots=shots, omit=[]))
    assert [g.split(":")[0] for g in got] == ["G-SHOTS plan"]
    assert cap.shot_faults(SimpleNamespace(shots=shots, omit=[28])) == []
