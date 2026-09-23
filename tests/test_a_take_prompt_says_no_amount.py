"""The take prompt tells H3 the camera's direction, never its distance.

Audit 2026-09-22, Tier 3 item 22: 42-47 amount phrases per episode ("travelling
a forearm", "pushes in on him a hand's breadth") went to a model measured to
obey 0 of 16 of them. The PLAN keeps them -- G-MOVE measures travel against
the shot's size -- so only the words sent to the model lose them; "with small
amplitude" is the one scale word H3 was seen to follow.
"""
import pytest

from studio.episode_ref_official import camera_sentence, camera_verb, without_amount
from studio.plan_gates import amount


@pytest.mark.parametrize("head, said", [
    ("pushes in toward his face with small amplitude until his head fills the middle of the "
     "picture, travelling a forearm",
     "pushes in toward his face with small amplitude until his head fills the middle of the picture"),
    ("pushes in on him a hand's breadth, a dolly with small amplitude, until his face fills the "
     "middle of the picture",
     "pushes in on him, a dolly with small amplitude, until his face fills the middle of the picture"),
    ("tilts up the face of the cottage to the window, travelling a hand's breadth, until the lit "
     "sash is in the middle of the picture",
     "tilts up the face of the cottage to the window, until the lit sash is in the middle of the picture"),
    ("rises from the lawn, travelling two long strides", "rises from the lawn"),
])
def test_every_amount_shape_the_plans_write_is_removed(head, said):
    assert without_amount(head) == said


def test_a_head_with_no_amount_is_untouched():
    head = "pans to the right along the road until the sentinel is at the centre"
    assert without_amount(head) == head


def test_the_camera_sentence_carries_the_direction_and_not_the_distance():
    motion = ("The camera pushes in on his face with small amplitude until it fills the middle "
              "of the picture, travelling a forearm; he looks up")
    text = camera_sentence(motion, 0, 4)
    assert "pushes in on his face with small amplitude" in text
    assert "forearm" not in text and "travelling" not in text


def test_the_plan_still_measures_the_amount_it_wrote():
    head = "The camera pushes in on his face, travelling a forearm"
    assert amount(head) == pytest.approx(2.5)
    assert "forearm" not in camera_verb(without_amount("pushes in on his face, travelling a forearm"))
