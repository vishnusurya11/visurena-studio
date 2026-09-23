"""A close-up of a person with no person in it is not a usable reference.

MEASURED 2026-09-22 on ep09 shot 22, the episode's BUTTON: a big close-up of
the hussar shouting over his shoulder came back as an empty burning garden,
and the panel gate printed `faces 0/1` and passed it. It counts faces only
against going OVER the planned number -- ep05's crowd shots taught it not to
punish extra faces -- and nobody ever asked it about going under.

The rule is narrow on purpose. At a wide or a medium a face can be too small
for a detector to find and the panel is still right; at a close or a
medium_close the face IS the picture, so its absence is the fault.
"""
from studio.panel_dq import verdict


def clean(**kw):
    base = dict(faces=[], planned=0, sharp=1.0, ink=0.0, tiled=0.0)
    base.update(kw)
    return verdict(**base)


def test_a_close_up_that_plans_a_face_and_has_none_is_a_fault():
    got = clean(faces=[], planned=1, size="close")
    assert "missing" in got["flags"]
    assert not got["passed"]


def test_a_medium_close_that_plans_a_face_and_has_none_is_a_fault():
    assert "missing" in clean(faces=[], planned=1, size="medium_close")["flags"]


def test_a_close_up_with_its_face_is_clean():
    assert clean(faces=[0.4], planned=1, size="close")["passed"]


def test_a_wide_that_plans_a_face_and_shows_none_is_not_a_fault():
    # a figure at a wide can be too small for a detector and the panel right
    assert "missing" not in clean(faces=[], planned=1, size="wide")["flags"]


def test_a_medium_is_not_held_to_it_either():
    assert "missing" not in clean(faces=[], planned=1, size="medium")["flags"]


def test_an_insert_plans_nobody_and_is_clean():
    assert clean(faces=[], planned=0, size="insert")["passed"]


def test_a_close_up_planning_nobody_is_clean():
    assert clean(faces=[], planned=0, size="close")["passed"]


def test_the_size_may_be_left_out_and_nothing_changes():
    assert clean(faces=[], planned=1)["passed"]
