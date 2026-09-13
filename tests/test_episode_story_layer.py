"""The story layer: the one question an episode answers, and the value each
shot turns.

From the screenwriting-skills reading, 2026-09-12 (Armstrong's Succession
scripts; McKee's scene design via sw-scene-craft):

  * "One core question per episode, answered inside the episode", written as
    "Today, can X do Y?".  Succession's fourth season holds to it every hour.
  * McKee: there is no scene without a turn.  Mark the value at the open and
    again at the close; if they are the same, the scene exists to explain
    something, and the fix is to delete it and weave the information elsewhere.

Both are OPTIONAL on the contract and REPORTED by a lint rather than refused,
because episode 1 was written before either existed and still has to validate.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from studio import episode_spec as spec
from studio import story_layer


def a_shot(index: int = 0, **kw) -> spec.Shot:
    base = dict(index=index, section="hook", setup="criterion", size="medium",
                frame="Watson stands at the bar", motion="He turns his head to the door")
    return spec.Shot(**{**base, **kw})


def test_a_shot_may_declare_the_value_it_turns():
    shot = a_shot(turn="alone -> seen")
    assert shot.turn == "alone -> seen"


def test_a_shot_may_carry_a_why_the_drawer_never_reads():
    """The why is for the people and agents writing the episode. It must not
    reach the model, so it is not one of the strings the sheet is built from."""
    shot = a_shot(why="Gives his name for the first time, and shows he is glad of it")
    assert shot.why and "why" not in spec.SHEET_TEXT


def test_a_why_may_say_what_something_is_not():
    """Every string the DRAWER reads must be affirmative; the why is reasoning,
    not a picture, so it is free to explain an absence."""
    a_shot(why="No crowd here, so the empty street reads as the hour")


def test_both_are_optional_so_an_older_plan_still_validates():
    shot = a_shot()
    assert shot.turn == "" and shot.why == ""


def test_the_episode_may_declare_the_one_question_it_answers():
    assert story_layer.question_shape("Today, can Watson find a man to share rooms with?")


def test_a_question_that_is_not_a_question_about_today_is_reported():
    assert not story_layer.question_shape("Watson looks for lodgings")
    assert not story_layer.question_shape("Can Watson find rooms?")


def test_the_lint_names_the_shots_that_turn_nothing():
    shots = [a_shot(0, turn="alone -> seen"), a_shot(1), a_shot(2, turn="hope -> refused")]
    assert story_layer.turnless(shots) == [1]


def test_a_shot_whose_value_ends_where_it_started_is_reported_too():
    """Same value on both sides is McKee's non-event: the shot is there to
    explain something, and explanation belongs in another shot's picture."""
    assert story_layer.turnless([a_shot(0, turn="alone -> alone")]) == [0]


def test_the_lint_reports_and_never_refuses():
    """Episode 1 predates the field; a story lint that raises would block a cut
    that is already made."""
    report = story_layer.report(spec_question="", shots=[a_shot(0)])
    assert report["turnless"] == [0] and report["question_ok"] is False
    assert report["passed"] is False and isinstance(report["says"], str)
