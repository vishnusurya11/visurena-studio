"""A bench with no owner labels says so (fleet H ruling A1, A15).

`wilson(0, 0)` used to return (0, 0): a gate nobody had labelled printed a
certain zero.  Nothing counted is the interval (0, 1), and every owner line of
the report carries its status -- unlabelled at n = 0, thin under the
convention's 30, armable at 30 or more -- so a gate with no labels prints
"NO LABELS" and "unarmed, n=0" instead of a number that reads like a finding.
"""
from pathlib import Path

from studio import judge_bench as jb

FIXTURES = Path(__file__).parent / "fixtures" / "judge_bench"


def defaults_only():
    return [r for r in jb.load_rows(FIXTURES, "take") if r.verdict_by != "owner"]


def test_wilson_of_nothing_is_the_unit_interval():
    assert jb.wilson(0, 0) == (0.0, 1.0)
    assert jb.interval(0, 0).low == 0.0 and jb.interval(0, 0).high == 1.0


def test_the_status_of_a_count_is_unlabelled_thin_or_armable():
    assert jb.status(0) == "unarmed, n=0 (NO LABELS)"
    assert jb.status(12) == "unarmed, n=12 (thin)"
    assert jb.status(30) == "armable, n=30"


def test_a_report_with_no_owner_rows_says_no_labels():
    outcomes = jb.run(defaults_only(), lambda r: {"refused": False, "classes": [], "values": {}})
    text = jb.report(outcomes, "fixture", "abcdef01")
    assert "NO LABELS" in text and "unarmed, n=0" in text


def test_a_report_with_owner_rows_prints_their_count():
    outcomes = jb.run(jb.load_rows(FIXTURES, "take"), lambda r: {"refused": True, "classes": [], "values": {}})
    assert "unarmed, n=2 (thin)" in jb.report(outcomes, "fixture", "abcdef01")
