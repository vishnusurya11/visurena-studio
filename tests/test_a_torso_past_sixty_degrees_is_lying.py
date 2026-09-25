"""Posture is a torso vector, not a caption.  The VLM read "lying" off the ground
under a man who stood; DWPose gives the hip-to-neck line and its angle from the
vertical is a number: past LYING degrees the man is down."""
import json
from pathlib import Path

from studio.measure import keypoints as kp

FIX = Path(__file__).parent / "fixtures" / "measures"


def _first_person(name: str):
    frames = kp.parse(json.dumps(json.load((FIX / name).open())))
    return kp.people(frames[0])[0]


def test_a_torso_past_sixty_degrees_is_lying():
    down = _first_person("dwpose_lying.json")
    assert kp.torso_angle(down) > kp.LYING
    assert kp.posture(down) == "lying"


def test_an_upright_torso_with_straight_knees_is_standing():
    up = _first_person("dwpose_standing.json")
    assert kp.torso_angle(up) < 5.0
    assert kp.posture(up) == "standing"


def test_a_person_with_no_torso_is_unread():
    assert kp.posture(kp.people({"people": [{"pose_keypoints_2d": [0.0] * 54}],
                                 "canvas_height": 512, "canvas_width": 512})[0]) == "unread"
