"""The turn is an action between two DIFFERENT named people of the turn
shot's setup, on the shot the plan marks, with a visible verb; the three
readings must agree on it.  Anything less is a `story` fault."""
from __future__ import annotations

from studio.judges import plan as plan_judge
from tests.plan_reader_fixtures import BRIEF, reading
from tests.test_episode_writer import canned_plan


def _kinds(verdict):
    return [f.kind for f in verdict.faults]


def test_a_turn_with_nobody_acted_on_is_a_story_fault():
    verdict = plan_judge.judge(canned_plan(), BRIEF, [reading("no_turn")] * 3)
    assert not verdict.passed and "story" in _kinds(verdict)
    assert verdict.faults[0].where == "shot_14"


def test_a_turn_on_oneself_is_a_story_fault():
    same = reading("good").model_copy(deep=True)
    same.turn.acted_on = "lead"
    verdict = plan_judge.judge(canned_plan(), BRIEF, [same] * 3)
    assert "story" in _kinds(verdict) and "two" in verdict.faults[0].note


def test_a_person_the_setup_does_not_hold_is_a_story_fault():
    stranger = reading("good").model_copy(deep=True)
    stranger.turn.acted_on = "nobody"
    verdict = plan_judge.judge(canned_plan(), BRIEF, [stranger] * 3)
    assert "story" in _kinds(verdict) and verdict.faults[0].evidence["cast"] == ["lead", "other"]


def test_a_verb_outside_the_acting_vocabulary_is_a_story_fault():
    looks = reading("good").model_copy(deep=True)
    looks.turn.verb = "looks"
    verdict = plan_judge.judge(canned_plan(), BRIEF, [looks] * 3)
    assert "story" in _kinds(verdict) and "looks" in verdict.faults[0].note


def test_a_turn_read_on_another_shot_than_the_plan_marks_is_a_story_fault():
    elsewhere = reading("good").model_copy(deep=True)
    elsewhere.turn.shot = 3
    verdict = plan_judge.judge(canned_plan(), BRIEF, [elsewhere] * 3)
    assert "story" in _kinds(verdict) and verdict.faults[0].evidence == {"read": 3, "marked": 14}


def test_readings_that_do_not_agree_on_the_turn_are_a_story_fault():
    one, two, three = (reading("good").model_copy(deep=True) for _ in range(3))
    two.turn.shot, three.turn.acted_on = 3, "lead"
    verdict = plan_judge.judge(canned_plan(), BRIEF, [one, two, three])
    assert "story" in _kinds(verdict) and "agree" in verdict.faults[0].note


def test_two_of_three_agreeing_is_the_turn():
    one, two, three = (reading("good").model_copy(deep=True) for _ in range(3))
    three.turn.shot = 3
    assert plan_judge.judge(canned_plan(), BRIEF, [one, two, three]).passed
