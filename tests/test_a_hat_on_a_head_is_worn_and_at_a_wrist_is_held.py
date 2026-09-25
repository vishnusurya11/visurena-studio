"""A hat is a box.  Over a head box it is worn; centred within reach of a wrist
it is held; a picture with one planned person doing both is the fault the plan
gate refuses in words and no picture gate counted."""
import json
from pathlib import Path

from studio.measure import boxes

FIX = Path(__file__).parent / "fixtures" / "measures"
SIZE = (512, 512)
FACE = {"cx": 0.5, "cy": 0.25, "h": 0.2, "score": 0.9}


def _hats():
    found = boxes.parse((FIX / "gdino_hats.json").read_text())
    heads = [boxes.head_box(FACE, aspect=1.0)]
    return boxes.hats(boxes.normalised(found, SIZE), heads, wrists=[(420 / 512, 330 / 512)], face_h=FACE["h"])


def test_a_hat_on_a_head_is_worn_and_at_a_wrist_is_held():
    states = [h["state"] for h in _hats()]
    assert states == ["worn", "held"]


def test_worn_and_held_on_one_planned_person_is_a_fault():
    assert boxes.hat_fault(_hats()) == "a hat worn and a hat held"
    assert boxes.hat_fault(_hats()[:1]) is None


def test_a_hat_near_nothing_is_loose():
    loose = boxes.hats([[0.05, 0.8, 0.15, 0.9]], [boxes.head_box(FACE, 1.0)], [], FACE["h"])
    assert loose[0]["state"] == "loose"
