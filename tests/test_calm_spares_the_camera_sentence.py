"""`calm()` rewrites the drawer's prose, never the camera sentence (shot framework D-a).

`calm` turns stillness words into positions ("holds" -> "keeps") because a block carrying two stillness
words froze 0.77 against 0.47.  It was applied to the motion head too, so the catalog's own camera words
reached the model as "The camera keeps a locked-off frame" (ep01 T10, T15, T26) and "The camera keeps over
<Subject 2>'s shoulder" (T13): a verb the camera catalog does not hold (prompt bench finding 3).  Every
camera sentence now opens on a catalog verb, and the lint allows the camera's own hold.

EXCEPT OVER A SHOULDER (proof 2026-10-21, docs/audit/2026-10-21_shot_framework/implement/RESULT.md): T13
re-rendered with "The camera holds over <Subject 2>'s shoulder" scored under its delivered take gate on 3 of 3
renders (42.2-42.8 vs 43.5), the pre-registered failure; the locked-off hold passed on T10, T15 and T26.  So
an over-the-shoulder head keeps its delivered "keeps over" until a bench says otherwise.
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


@pytest.mark.parametrize("index", [10, 15, 26])
def test_every_camera_sentence_parses_to_a_catalog_id(index):
    said = [v for v in camera_verbs(sf.take_prompt(index)) if v != "is"]
    assert said and set(said) <= CATALOG_VERBS, said


def test_holds_a_locked_off_frame_survives():
    assert "The camera holds a locked-off frame" in sf.detailed(sf.take_prompt(10))


def test_an_over_the_shoulder_head_keeps_its_delivered_words():
    assert "The camera keeps over <Subject 2>'s shoulder" in sf.detailed(sf.take_prompt(13))
    assert ro.calm("The camera holds over the lawyer's shoulder") == "The camera keeps over the lawyer's shoulder"


def test_calm_still_rewrites_the_drawers_holds():
    assert ro.calm("his hand holds the cane") == "his hand keeps the cane"
    assert ro.calm("The camera holds a locked-off frame") == "The camera holds a locked-off frame"


def test_the_stillness_lint_allows_the_cameras_own_hold_only():
    assert ro.l2_stillness("The camera holds a locked-off frame as he turns.", {}) == []
    assert ro.l2_stillness("The camera holds a locked-off frame as he holds the cane.", {}) != []
