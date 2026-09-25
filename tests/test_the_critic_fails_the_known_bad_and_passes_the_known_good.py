"""The fixture lock: with canned readings, the known-good scrubbed plan
passes and the known-bad one fails -- and fails even on the GOOD reading,
because its turn setup holds one person and its answer names nothing.  A
judge that cannot tell these two apart is not the judge."""
from __future__ import annotations

from studio.episode_spec import Episode
from studio.judges import plan as plan_judge
from tests.plan_reader_fixtures import BRIEF, plan, reading


def test_both_plans_load_under_the_contract():
    assert Episode.model_validate(plan("known_good")).number == 3
    assert Episode.model_validate(plan("known_bad")).number == 3


def test_the_known_good_passes_on_the_good_reading():
    verdict = plan_judge.judge(plan("known_good"), BRIEF, [reading("good")] * 3)
    assert verdict.passed, verdict.summary()


def test_the_known_bad_fails_on_the_good_reading():
    """The code judges the plan, not the reader's goodwill: the acted-on person
    is not in the turn shot's setup."""
    verdict = plan_judge.judge(plan("known_bad"), BRIEF, [reading("good")] * 3)
    assert not verdict.passed and "story" in [f.kind for f in verdict.faults]


def test_the_known_bad_fails_on_its_own_readings():
    verdict = plan_judge.judge(plan("known_bad"), BRIEF, [reading("no_answer")] * 3)
    kinds = [f.kind for f in verdict.faults]
    assert "story" in kinds and "answer" in kinds


def test_the_known_good_fails_only_when_the_reading_finds_no_answer():
    verdict = plan_judge.judge(plan("known_good"), BRIEF, [reading("no_answer")] * 3)
    assert [f.kind for f in verdict.faults] == ["answer"]


def test_an_answer_on_a_line_the_plan_lacks_is_an_answer_fault():
    ghost = reading("good").model_copy(deep=True)
    ghost.answer.index = 99
    verdict = plan_judge.judge(plan("known_good"), BRIEF, [ghost] * 3)
    assert [f.kind for f in verdict.faults] == ["answer"] and "99" in verdict.faults[0].note


def test_faults_come_back_as_gate_lines_for_the_writer():
    verdict = plan_judge.judge(plan("known_bad"), BRIEF, [reading("no_answer")] * 3)
    lines = plan_judge.lines(verdict)
    assert lines and all(line.startswith("G-READER ") for line in lines)
    assert any("shot 14" in line for line in lines)
