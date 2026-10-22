"""Wave 1 review findings 2 and 3: G-MUTE and its cure read the verb's sense (craft ruling A8).

Finding 2: SPEECH_VERB had no negation and no sense check, so "Hyde said nothing" and "she answers
the door" counted as a moving mouth.  A verb under a negation, before "nothing" / "no word", or
answering a door, bell or knock is a silent face.
Finding 3: `mute_listens` swapped every verb for its "listens" form, so a verb with an object came
out garbled ("Enfield tells Utterson the story" -> "Enfield listens Utterson the story"), the class
A18 removes.  The cure now rewrites only a verb with no object after it; any other is left as written
and the row keeps firing on it.  Synthetic shots plus tests/fixtures/craft ep01.  No spend."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from studio import plan_cures, screenplay_grammar as sg

CRAFT = Path(__file__).parent / "fixtures" / "craft"


def plan_of(frame: str) -> dict:
    return {"shots": [{"index": 0, "size": "medium", "faces": ["hyde"], "frame": frame}], "lines": []}


@pytest.mark.parametrize("frame", [
    "Hyde said nothing, his hand on the key.",
    "She answers the door with a lamp.",
    "He does not speak; he stares at the gable.",
    "Poole stands without a word, as if to say nothing.",
    "No one speaks in the dark court.",
    "Utterson never answers him.",
])
def test_a_silent_face_is_not_a_speaking_one(frame):
    assert sg.mute_faults(plan_of(frame)) == []


@pytest.mark.parametrize("frame", ["Hyde speaks quietly at the door.", "Enfield tells Utterson the story."])
def test_a_speaking_face_still_fires(frame):
    assert [f.split(":")[0] for f in sg.mute_faults(plan_of(frame))] == ["G-MUTE shot 0"]


@pytest.mark.parametrize("frame", [
    "Enfield tells Utterson the story.",
    "He asks the lawyer a question.",
    "Enfield answers him with a nod.",
])
def test_the_cure_never_writes_a_verb_with_an_object_into_listens(frame):
    cured = plan_cures.mute_listens(plan_of(frame), [0])
    assert cured["shots"][0]["frame"] == frame
    assert sg.mute_faults(cured)                              # left as written, so it still reports


def test_a_verb_with_no_object_listens():
    cured = plan_cures.mute_listens(plan_of("Hyde speaks quietly, then speaking to Poole, he answers."), [0])
    assert cured["shots"][0]["frame"] == "Hyde listens quietly, then listening to Poole, he listens."


def test_a_silent_verb_is_not_rewritten():
    cured = plan_cures.mute_listens(plan_of("Hyde said nothing as Enfield speaks."), [0])
    assert cured["shots"][0]["frame"] == "Hyde said nothing as Enfield listens."


def test_ep01_still_fires_on_13_and_15_and_still_cures():
    plan = json.loads((CRAFT / "episodes" / "ep01" / "plan.json").read_text(encoding="utf-8"))
    assert [f.split(":")[0] for f in sg.mute_faults(plan)] == ["G-MUTE shot 13", "G-MUTE shot 15"]
    assert sg.mute_faults(plan_cures.mute_listens(copy.deepcopy(plan), [13, 15])) == []
