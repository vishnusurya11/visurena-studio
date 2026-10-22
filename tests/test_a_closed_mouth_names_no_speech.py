"""A block whose mouth is closed names no speech verb (shot framework D-b).

Jekyll Kawajiri ep01 T13 is a silent track (narration over Enfield at the door), and its motion was
written "the man about town speaks and taps his black walking cane".  The take said "<Subject 1> speaks"
in the camera sentence and "<Subject 1>'s mouth is closed from 00:00 to 00:08 while he speaks" in the
next: a plain contradiction (prompt bench finding 3).  A spoken take keeps its speech verb: the lip drive
carries it (T11, "speaks with a cold grin").  Fixture: tests/fixtures/shot_framework/."""
from __future__ import annotations

import re

import shot_framework_fixtures as sf

SPEECH = re.compile(r"\b(?:speaks?|speaking|talks?|talking)\b", re.I)


def test_the_delivered_t13_said_both():
    body = sf.detailed(sf.delivered(13))
    assert SPEECH.search(body) and "mouth is closed" in body


def test_t13_silent_track_has_no_speaks():
    body = sf.detailed(sf.take_prompt(13))
    assert not SPEECH.search(body)
    assert "mouth is closed" in body
    assert "taps his black walking cane on the flagstones" in body


def test_a_spoken_take_keeps_its_speech_verb():
    assert "speaks with a cold grin" in sf.detailed(sf.take_prompt(11))
