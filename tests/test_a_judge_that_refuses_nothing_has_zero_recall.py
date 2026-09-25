"""A judge that refuses nothing catches nothing: recall 0 on every fault row.

The bench's recall is the share of fault rows the judge refused, pooled and
per owner / all; a judge that passes everything is the floor every real
judge must clear.  Its misses are every fault row it was shown.
"""
from pathlib import Path

from studio import judge_bench as jb

FIXTURES = Path(__file__).parent / "fixtures" / "judge_bench"


def passes_everything(row):
    return {"refused": False, "classes": [], "values": {}}


def test_recall_is_zero_on_owner_and_on_all():
    outcomes = jb.run(jb.load_rows(FIXTURES, "take"), passes_everything)
    assert jb.recall(outcomes, by="owner").point == 0.0
    assert jb.recall(outcomes, by="all").point == 0.0
    assert jb.recall(outcomes, by="owner").n == 2


def test_every_fault_row_is_a_miss():
    outcomes = jb.run(jb.load_rows(FIXTURES, "take"), passes_everything)
    assert len(jb.misses(outcomes)) == 4          # two owner catches, one agent class, one agent reject
    assert jb.false_refusals(outcomes).point == 0.0


def test_load_rows_keeps_one_kind_and_drops_the_unverified():
    rows = jb.load_rows(FIXTURES, "take")
    assert {r.kind for r in rows} == {"take"}
    assert not any(r.verdict_by == "unverified" for r in rows)


def cannot_measure(row):
    return {"refused": False, "classes": [], "values": {"note": "not measured"}}


def test_a_row_the_judge_has_no_inputs_for_is_neither_a_miss_nor_a_catch():
    outcomes = jb.run(jb.load_rows(FIXTURES, "take"), cannot_measure)
    assert jb.unmeasured(outcomes) == len(outcomes)
    assert jb.recall(outcomes, by="owner").n == 0 and jb.misses(outcomes) == []
