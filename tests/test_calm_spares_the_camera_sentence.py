"""`calm()` rewrites the drawer's prose, never the camera sentence (shot framework D-a).

`calm` turns stillness words into positions ("holds" -> "keeps") because a block carrying two stillness
words froze 0.77 against 0.47.  It was applied to the motion head too, so the catalog's own camera words
reached the model as "The camera keeps a locked-off frame" (ep01 T10, T15, T26) and "The camera keeps over
<Subject 2>'s shoulder" (T13): a verb the camera catalog does not hold (prompt bench finding 3).  Every
camera sentence now opens on a catalog verb, and the lint allows the camera's own hold.
Fixture: tests/fixtures/shot_framework/."""
from __future__ import annotations

import re

import pytest

import shot_framework_fixtures as sf
from studio import episode_ref_official as ro

CATALOG_VERBS = {"holds", "pushes", "pulls", "tracks", "pans", "tilts", "rises", "cranes", "descends",
                 "dollies", "zooms", "orbits", "moves", "racks", "trucks"}
"""docs/calibration/camera_catalog.md's verbs, third person, as `plan_gates.MOVE_VERBS` reads them."""


def camera_verbs(text: str) -> list[str]:
    return re.findall(r"\bThe camera (\w+)", sf.detailed(text))


@pytest.mark.parametrize("index", [10, 13, 15, 26])
def test_the_delivered_takes_said_keeps(index):
    assert "keeps" in camera_verbs(sf.delivered(index))


@pytest.mark.parametrize("index", [10, 13, 15, 26])
def test_every_camera_sentence_parses_to_a_catalog_id(index):
    said = [v for v in camera_verbs(sf.take_prompt(index)) if v != "is"]
    assert said and set(said) <= CATALOG_VERBS, said


def test_holds_a_locked_off_frame_survives():
    assert "The camera holds a locked-off frame" in sf.detailed(sf.take_prompt(10))
    assert "The camera holds over <Subject 2>'s shoulder" in sf.detailed(sf.take_prompt(13))


def test_calm_still_rewrites_the_drawers_holds():
    assert ro.calm("his hand holds the cane") == "his hand keeps the cane"
    assert ro.calm("The camera holds a locked-off frame") == "The camera holds a locked-off frame"


def test_the_stillness_lint_allows_the_cameras_own_hold_only():
    assert ro.l2_stillness("The camera holds a locked-off frame as he turns.", {}) == []
    assert ro.l2_stillness("The camera holds a locked-off frame as he holds the cane.", {}) != []
