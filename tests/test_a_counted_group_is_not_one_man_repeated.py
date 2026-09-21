"""A panel that names a COUNT of unnamed people must say they differ.

MEASURED 2026-09-20 on ep06 `knots` shot 10, the first render after the dolls
and the figure-framing were fixed. The shot reads "three young men at the back
of the crowd, shoulder to shoulder and grinning, hands cupped round their
mouths, in cheap dark suits and bowlers". Three men, ONE wardrobe. It came
back as the same man drawn three times: one face, one bowler, one gesture.

`no_duplicates` binds the NAMED cast and says nothing about a counted group of
walk-ons, because a walk-on has no sheet and no name to bind. The count itself
is the hook.

Said positively -- each has his own -- never "no two are alike", which is the
fence the models read as an instruction to make them alike.
"""
from __future__ import annotations

import pytest

from studio.storyboard_grid import varied_group


@pytest.mark.parametrize("body,count", [
    ("Medium close on three young men at the back of the crowd", "three"),
    ("Two women in shawls at the roadside", "two"),
    ("Wide on five of them closing up shoulder to shoulder", "five"),
    ("Four policemen holding the line", "four"),
])
def test_a_counted_group_is_told_its_members_differ(body, count):
    said = varied_group(body)
    assert said, f"no clause for {body!r}"
    assert count in said.lower()


@pytest.mark.parametrize("body", [
    "Wide on the empty common at night",
    "Insert on a nosebag hanging from a bridle",
    "Medium close on the narrator alone on the road",
])
def test_a_panel_with_no_counted_group_says_nothing(body):
    assert varied_group(body) == ""


def test_the_clause_is_positive():
    said = varied_group("three young men grinning").lower()
    for fence in ("no two", "not alike", "never the same", "do not"):
        assert fence not in said, f"builds a fence: {said}"


def test_the_clause_names_what_differs():
    said = varied_group("three young men grinning").lower()
    assert "face" in said and "build" in said


def test_one_person_is_not_a_group():
    assert varied_group("One man alone on the road") == ""
