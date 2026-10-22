"""One interval helper for every bench (fleet H ruling A3): the exact
Clopper-Pearson bound, one-sided and two-sided, and the Wilson score interval.

At the counts a casebook has -- tens of owner rows -- the normal approximation
lies, so a promotion bar ("one-sided CP lower bound 0.80 at n >= 30") is read
off the exact binomial.  Nothing counted is no knowledge: (0, 1), never (0, 0).
"""
import pytest

from studio import intervals


def test_the_one_sided_upper_bound_of_no_faults_in_sixty_is_about_five_percent():
    assert intervals.cp_upper(0, 60) == pytest.approx(0.049, abs=0.0005)
    assert intervals.cp_upper(0, 30) == pytest.approx(0.095, abs=0.0005)


def test_the_one_sided_lower_bound_of_26_in_30_is_0_72():
    assert intervals.cp_lower(26, 30) == pytest.approx(0.720, abs=0.0005)
    assert intervals.cp_lower(0, 30) == 0.0 and intervals.cp_upper(30, 30) == 1.0


def test_the_two_sided_interval_spends_half_the_error_on_each_side():
    low, high = intervals.clopper_pearson(26, 30)
    assert low == pytest.approx(intervals.cp_lower(26, 30, conf=0.975), abs=1e-4)
    assert high == pytest.approx(intervals.cp_upper(26, 30, conf=0.975), abs=1e-4)
    assert low < 26 / 30 < high


def test_nothing_counted_is_the_whole_unit_interval():
    assert intervals.clopper_pearson(0, 0) == (0.0, 1.0)
    assert intervals.wilson(0, 0) == (0.0, 1.0)
    assert intervals.cp_lower(0, 0) == 0.0 and intervals.cp_upper(0, 0) == 1.0


def test_wilson_matches_the_design_gate_values():
    low, _ = intervals.wilson(26, 30)
    assert low == pytest.approx(0.703, abs=0.001)


def test_a_count_outside_its_trials_is_refused():
    with pytest.raises(ValueError):
        intervals.cp_upper(5, 4)
