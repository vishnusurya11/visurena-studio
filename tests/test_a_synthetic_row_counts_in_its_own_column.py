"""A synthetic row never counts toward the owner bar; it has its own column.

A corruption drawn to prove a detector can see a fault at all is not the
owner's catch.  It weighs nothing in recall on owner or all rows, and the
confusion table and the report carry it separately.
"""
from pathlib import Path

from studio import judge_bench as jb

FIXTURES = Path(__file__).parent / "fixtures" / "judge_bench"


def synthetic_only(row):
    return {"refused": row.verdict_by == "synthetic", "classes": ["lettering"], "values": {}}


def test_a_caught_synthetic_row_moves_no_owner_or_all_recall():
    outcomes = jb.run(jb.load_rows(FIXTURES, "panel"), synthetic_only)
    assert jb.recall(outcomes, by="owner").n == 0
    assert jb.recall(outcomes, by="all").n == 0
    assert jb.recall(outcomes, by="synthetic").point == 1.0


def test_the_confusion_table_keeps_a_synthetic_column():
    outcomes = jb.run(jb.load_rows(FIXTURES, "panel"), synthetic_only)
    cell = jb.confusion(outcomes)["lettering"]
    assert cell["tp"] == 0 and cell["synthetic_tp"] == 1 and cell["synthetic_n"] == 1


def test_the_report_names_the_column():
    outcomes = jb.run(jb.load_rows(FIXTURES, "panel"), synthetic_only)
    text = jb.report(outcomes, "fixture", "abcdef01")
    assert "synthetic" in text
