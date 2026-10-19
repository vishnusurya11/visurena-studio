"""studio/unit_buckets.py: every unit of a step sits in exactly one bucket and the buckets
sum to the plan's total (Jekyll Kawajiri ep01: 28 takes, 22 lines).  Pure; $0."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from studio import unit_buckets as ub

FIX = Path(__file__).resolve().parent / "fixtures" / "ep01_ledger"


def _plan() -> dict:
    return json.loads((FIX / "plan_counts.json").read_text(encoding="utf-8"))


def test_the_totals_come_from_the_plan_not_the_files():
    assert ub.plan_totals({"shots": [{}] * 28, "lines": [{}] * 22}) == {"takes": 28, "lines": 22}
    assert ub.plan_totals(_plan()) == {"takes": 28, "lines": 22}


@pytest.mark.parametrize("facts, word", [
    ({"running": True, "file": True}, "running"),
    ({"blocked": True}, "blocked"),
    ({}, "not started"),
    ({"file": True, "stale": True}, "to redo"),
    ({"file": True, "failed": True}, "to fix"),
    ({"file": True}, "to check"),
    ({"file": True, "judged": True, "flagged": True}, "kept with flags"),
    ({"file": True, "judged": True}, "passed"),
])
def test_a_unit_has_one_plain_word(facts, word):
    assert ub.bucket_of(facts) == word


def test_the_buckets_sum_to_the_plan_total():
    units = [(f"T{i:02d}", {"file": True, "judged": True}) for i in range(1, 20)]
    units += [("T20", {"file": True, "stale": True}), ("T21", {"running": True})]
    got = ub.partition(units, 28)
    assert sum(got.values()) == 28 and got["passed"] == 19 and got["to redo"] == 1
    assert got["not started"] == 7                    # the units no file or row has met yet


def test_a_unit_in_two_buckets_raises():
    with pytest.raises(ValueError, match="T01"):
        ub.partition([("T01", {"file": True}), ("T01", {"running": True})], 28)


def test_more_units_than_the_plan_has_raises():
    with pytest.raises(ValueError, match="total"):
        ub.partition([(f"T{i}", {}) for i in range(3)], 2)


def test_the_words_line_names_only_the_buckets_that_hold_units():
    got = {w: 0 for w in ub.WORDS} | {"passed": 24, "to redo": 2, "to check": 2}
    assert ub.words(got) == "24 passed · 2 to check · 2 to redo"
