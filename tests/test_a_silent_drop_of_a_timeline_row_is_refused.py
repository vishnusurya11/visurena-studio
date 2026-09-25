"""Every row of the chapter (its scenes, as the brief lists them) is shown by
a shot or told by a line; a row with neither is silently dropped, and that
is a `coverage` fault.  A row the reading never mentions is dropped too."""
from __future__ import annotations

from studio.judges import plan as plan_judge
from tests.plan_reader_fixtures import BRIEF, reading
from tests.test_episode_writer import canned_plan


def test_a_row_with_no_shot_and_no_line_is_a_coverage_fault():
    verdict = plan_judge.judge(canned_plan(), BRIEF, [reading("dropped")] * 3)
    assert not verdict.passed
    fault = verdict.faults[0]
    assert fault.kind == "coverage" and fault.where == "row_1"
    assert "One hands the other a cup" in fault.note


def test_a_row_the_reading_never_mentions_is_dropped():
    short = reading("good").model_copy(deep=True)
    short.coverage = short.coverage[:1]
    verdict = plan_judge.judge(canned_plan(), BRIEF, [short] * 3)
    assert [f.where for f in verdict.faults] == ["row_1"]


def test_a_row_told_by_a_line_alone_is_covered():
    told = reading("dropped").model_copy(deep=True)
    told.coverage[1].lines = [14]
    assert plan_judge.judge(canned_plan(), BRIEF, [told] * 3).passed


def test_a_covering_shot_the_plan_does_not_have_is_a_coverage_fault():
    ghost = reading("good").model_copy(deep=True)
    ghost.coverage[1].shots = [99]
    verdict = plan_judge.judge(canned_plan(), BRIEF, [ghost] * 3)
    assert verdict.faults[0].kind == "coverage" and "99" in verdict.faults[0].note


def test_the_chapter_rows_are_the_briefs_scene_summaries():
    assert plan_judge.rows_of(BRIEF) == ["Two people meet in a plain room.",
                                         "One hands the other a cup and speaks."]
    assert plan_judge.rows_of({"number": 3}) == []
