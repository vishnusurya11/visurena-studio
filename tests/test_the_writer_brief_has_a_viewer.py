"""The writer's brief has an audience (Jekyll ep01 review, 2026-10-13): it said
"Nothing you write is read by a person first. Write for the instruments", and
every rule served a downstream model -- none served a viewer.  Five viewer
rules now sit in the brief, each tied to its gate, and the voice section
names the book's narrator and the tale.  $0."""
from __future__ import annotations

import re

from agents import episode_writer as ew


def _section(text: str, heading: str) -> str:
    return text.split(heading, 1)[1].split("\n## ", 1)[0]


def test_the_brief_has_five_viewer_rules_each_tied_to_a_gate():
    viewer = _section(ew.load_skill(), "## The viewer")
    rules = re.findall(r"^\d\. \*\*(.+?)\*\*", viewer, re.M)
    assert rules == ["Hook in the first shot.", "The spike is shown.", "The teller tells his own tale.",
                     "Hold after every reveal.", "Withhold what the chapter withholds."]
    for gate in ("G-HOOK", "G-SPIKE", "G-ACTION", "G-PACE"):
        assert gate in viewer, gate


def test_the_brief_no_longer_writes_only_for_the_instruments():
    assert "Write for the instruments." not in ew.load_skill()


def test_the_voice_is_the_books_narrator_and_a_tale_is_a_kind():
    voice = _section(ew.load_skill(), "## The voice")
    assert "THE BOOK'S NARRATOR" in voice and "never choose a narrator yourself" in voice
    assert '`tale`' in voice


def test_dialogue_is_held_in_the_brief():
    assert "**Dialogue is held.**" in ew.load_skill() and "G-TALK" in ew.load_skill()
