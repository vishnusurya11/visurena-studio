"""A grid panel with named people AND declared extras says both.

Jekyll Kawajiri ep01 shot 18 (2026-10-18): `_who_v2` returned the named people alone whenever any
were named, so the three Sunday walkers declared as extras were never told to the grid."""
import json
from pathlib import Path

from studio.storyboard_grid import _who_v2

PLAN = json.loads((Path(__file__).parent / "fixtures" / "ep01_replay" / "P03" / "plan.json").read_text("utf-8"))
SHOT = next(s for s in PLAN["shots"] if s["index"] == 18)


def test_extras_beside_named_people_are_said():
    said = _who_v2(["the lawyer", "the cousin"], SHOT["extras"])
    assert said == "In it: the lawyer; the cousin; and 3 unnamed distant people, none of them a named person."


def test_one_extra_is_a_person():
    assert _who_v2(["the lawyer"], 1) == \
        "In it: the lawyer; and 1 unnamed distant person, none of them a named person."


def test_named_people_alone_are_unchanged():
    assert _who_v2(["the lawyer"], 0) == "In it: the lawyer."


def test_extras_alone_and_the_empty_place_are_unchanged():
    assert _who_v2([], 2) == "In it: 2 unnamed people, none of them a named person."
    assert _who_v2([], 0).startswith("It is a picture of the place alone")
