"""The camera verb is never garbled into an arrival noun, and the take keeps its verb count (shot framework D-d).

ep01 T06 ended "By 00:07 the camera is tilting up through the last frame, with the camera tilts up now in
frame": its written `end` names "the corner gas lamp", `is_layout` read "corner" as a frame corner, and the
arrival lent the camera clause as a noun.  An end that is the camera's own sentence is no layout; it trails
the arrival as its own clause.  The gavel HELD the verb's count (D-d count waits for bench R2-3: B2's camera
nearly held when the verb was said once), so the repair keeps all three tilt mentions.
Fixture: tests/fixtures/shot_framework/."""
from __future__ import annotations

import re

import shot_framework_fixtures as sf
from studio import episode_ref_official as ro

TILT = re.compile(r"\btilt(?:s|ing)? up\b")


def test_the_delivered_t06_was_garbled():
    assert "with the camera tilts up now in frame" in sf.detailed(sf.delivered(6))


def test_t06_has_no_with_the_camera_tilts_up_now():
    assert "with the camera" not in sf.detailed(sf.take_prompt(6))


def test_t06_keeps_its_verb_count():
    assert len(TILT.findall(sf.detailed(sf.take_prompt(6)))) == len(TILT.findall(sf.detailed(sf.delivered(6)))) == 3


def test_a_camera_end_is_no_layout_but_a_frame_corner_still_is():
    assert not ro.is_layout("The camera tilts up from the cobbles to the corner gas lamp")
    assert ro.is_layout("The lamp stands in the top corner of the frame")
