"""DWPose reports a stray limb as a headless extra person.  More wrists (or
ankles) than two per head is an extra limb, by count, not by looking."""
import json
from pathlib import Path

from studio.measure import keypoints as kp

FIX = Path(__file__).parent / "fixtures" / "measures"


def test_a_third_wrist_is_an_extra_limb():
    frame = json.load((FIX / "dwpose_third_wrist.json").open())[0]
    counts = kp.limbs(frame)
    assert counts == {"heads": 1, "wrists": 3, "ankles": 2}
    assert kp.extra_limbs(frame) == ["3 wrists for 1 head"]


def test_two_wrists_on_one_head_is_no_extra_limb():
    frame = json.load((FIX / "dwpose_standing.json").open())[0]
    assert kp.extra_limbs(frame) == []


def test_wrists_are_the_visible_ones():
    person = kp.people(json.load((FIX / "dwpose_medium_close.json").open())[0])[0]
    assert len(kp.wrists(person)) == 2
