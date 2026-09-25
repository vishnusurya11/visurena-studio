"""Recall is reported with its Wilson interval, because n is 1-3 per class.

A point of 1.0 on two rows is not a wall to trust; the interval says how
wide the ignorance is.  The bounds sit inside [0, 1] around the point and
tighten as n grows.
"""
from pathlib import Path

from studio import judge_bench as jb

FIXTURES = Path(__file__).parent / "fixtures" / "judge_bench"


def slides_only(row):
    return {"refused": row.fault_class == "anchored_slide", "classes": ["anchored_slide"], "values": {}}


def test_the_interval_brackets_the_point():
    outcomes = jb.run(jb.load_rows(FIXTURES, "take"), slides_only)
    r = jb.recall(outcomes, by="owner")
    assert r.n == 2 and r.k == 1 and r.point == 0.5
    assert 0.0 <= r.low < r.point < r.high <= 1.0


def test_a_perfect_score_on_few_rows_has_a_low_bound_well_under_one():
    low, high = jb.wilson(2, 2)
    assert high == 1.0 and low < 0.5


def test_more_rows_tighten_the_interval():
    narrow = jb.wilson(20, 20)
    wide = jb.wilson(2, 2)
    assert narrow[0] > wide[0]


def test_no_rows_is_an_empty_interval_not_a_division():
    assert jb.wilson(0, 0) == (0.0, 0.0)
    assert jb.recall([], by="owner").n == 0
