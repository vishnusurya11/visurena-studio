"""Shot size is the lowest body keypoint in frame: ankles make a full, hips a
medium, shoulders alone a medium close, a head alone a close.  A medium close
drawn as a full figure is the framing fault the panel gate never named."""
import json
from pathlib import Path

from studio.measure import keypoints as kp

FIX = Path(__file__).parent / "fixtures" / "measures"


def _person(name: str):
    return kp.people(json.load((FIX / name).open())[0])[0]


def test_ankles_in_frame_is_not_a_medium_close():
    full = _person("dwpose_standing.json")
    assert kp.shot_size(full) == "full"
    assert kp.size_fault(kp.shot_size(full), "medium_close") is not None


def test_shoulders_without_hips_is_a_medium_close():
    assert kp.shot_size(_person("dwpose_medium_close.json")) == "medium_close"
    assert kp.size_fault("medium_close", "medium_close") is None


def test_a_medium_against_a_medium_close_is_one_step_and_no_fault():
    assert kp.size_fault("medium", "medium_close") is None
    assert kp.size_fault("close", "wide") is not None
