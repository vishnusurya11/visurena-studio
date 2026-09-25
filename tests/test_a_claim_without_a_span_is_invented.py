"""A count, a posture, a prop or a place the plan asserts about the chapter
carries the chapter's own words, or it was invented.  The readings' claims
are taken as a UNION (for recall): a claim any reading lists without a span
is invented; a span the chapter text does not contain is invented too."""
from __future__ import annotations

from studio.judges import plan as plan_judge
from tests.plan_reader_fixtures import BRIEF, reading
from tests.test_episode_writer import canned_plan


def test_a_claim_with_no_span_is_invented():
    bare = reading("good").model_copy(deep=True)
    bare.claims[0].span = ""
    verdict = plan_judge.judge(canned_plan(), BRIEF, [bare] * 3)
    assert not verdict.passed
    fault = verdict.faults[0]
    assert fault.kind == "invented" and fault.where == "shot_14" and "the cup" in fault.note


def test_one_reading_without_the_span_is_enough():
    good, bare = reading("good"), reading("good").model_copy(deep=True)
    bare.claims[0].span = ""
    verdict = plan_judge.judge(canned_plan(), BRIEF, [good, good, bare])
    assert [f.kind for f in verdict.faults] == ["invented"]


def test_a_span_the_chapter_does_not_contain_is_invented():
    made_up = reading("good").model_copy(deep=True)
    made_up.claims[0].span = "eight riders waited at the turn of the road"
    verdict = plan_judge.judge(canned_plan(), BRIEF, [made_up] * 3)
    assert verdict.faults[0].kind == "invented" and "not in the chapter" in verdict.faults[0].note
    assert verdict.faults[0].evidence["wall"] == plan_judge.SPAN_MATCH


def test_without_a_chapter_text_a_span_is_taken_as_written():
    brief = {k: v for k, v in BRIEF.items() if k != "chapter_text"}
    assert plan_judge.judge(canned_plan(), brief, [reading("good")] * 3).passed


def test_a_claim_on_a_shot_the_plan_lacks_is_invented():
    ghost = reading("good").model_copy(deep=True)
    ghost.claims[0].shot = 99
    verdict = plan_judge.judge(canned_plan(), BRIEF, [ghost] * 3)
    assert verdict.faults[0].kind == "invented" and verdict.faults[0].where == "shot_99"
