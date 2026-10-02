"""ep16 published cut (2026-10-02, deleted): every face-bearing prompt carried
<Subject 1> AND 2-4 untagged "the brother's hand/forearm" -- the possessive
guard (?!'s), added so "the narrator's wife" never binds the narrator, also
skipped the brother's OWN body parts, so the pinned man and a separately
named stranger coexisted in one prompt and H3 drew him twice in most shots.
tagged() now tags a face's own possessive; a display that is the PREFIX of
another cast member's display (the wife case) still never binds."""
from __future__ import annotations

import pytest

from studio import episode_ref_official as ro


@pytest.fixture(autouse=True)
def cast():
    saved = dict(ro.DISPLAY), set(ro.WOMEN)
    ro.DISPLAY.update({"narrators_brother": "the brother",
                       "narrator": "the narrator",
                       "narrators_wife": "the narrator's wife"})
    yield
    ro.DISPLAY.clear(); ro.DISPLAY.update(saved[0])
    ro.WOMEN.clear(); ro.WOMEN.update(saved[1])


def test_a_faces_own_possessive_is_tagged():
    got = ro.tagged("the brother's forearm reaches across the seat", ["narrators_brother"])
    assert got == "<Subject 1>'s forearm reaches across the seat"


def test_anothers_possessive_phrase_still_never_binds_the_owner():
    got = ro.tagged("the narrator's wife stands alone", ["narrator"])
    assert "<Subject 1>" not in got        # she is the wife, not him (ep09 T17)


def test_the_wife_binds_her_whole_phrase_when_she_is_the_face():
    got = ro.tagged("the narrator's wife stands alone", ["narrators_wife"])
    assert got.startswith("<Subject 1>")
