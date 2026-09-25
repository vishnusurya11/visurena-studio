"""A judge that refuses everything has a false-refusal rate of 1.

The false-refusal rate is the weighted share of pass rows the judge refused
(owner 1, agent 0.75, default 0.5).  Refusing every row buys full recall at
the price of every pass row -- the other floor, and the cost the report
prices in GPU minutes.
"""
from pathlib import Path

from studio import judge_bench as jb

FIXTURES = Path(__file__).parent / "fixtures" / "judge_bench"


def refuses_everything(row):
    return {"refused": True, "classes": ["unknown"], "values": {}}


def test_false_refusals_are_total_and_recall_is_full():
    outcomes = jb.run(jb.load_rows(FIXTURES, "take"), refuses_everything)
    assert jb.false_refusals(outcomes).point == 1.0
    assert jb.recall(outcomes, by="owner").point == 1.0
    assert jb.misses(outcomes) == []


def test_a_refusal_is_priced_in_gpu_minutes():
    outcomes = jb.run(jb.load_rows(FIXTURES, "take"), refuses_everything)
    assert jb.gpu_minutes(outcomes) == 7.0 * len(outcomes)
    assert jb.flag_rate(outcomes)["share"] == 1.0
    assert jb.flag_rate(outcomes)["per_unit"] == {"00000000000000/ep01": len(outcomes)}
