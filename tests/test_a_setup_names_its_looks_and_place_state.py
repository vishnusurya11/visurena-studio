"""The contract carries the continuity choices (decision 2026-10-10): a setup
names a person whose look is not the chapter's default, and what has changed
about its place; both default empty, so every existing plan still reads, and
the writer's strict-schema draft carries them as plain objects."""
from __future__ import annotations

from agents.episode_writer import Draft
from studio.episode_spec import Setup

BASE = {"described": "A study lit from the window at the left."}


def test_both_default_empty():
    s = Setup.model_validate(BASE)
    assert s.looks == [] and s.place_state == ""


def test_a_setup_names_a_look_and_a_state():
    s = Setup.model_validate({**BASE, "looks": [{"who": "narrator", "look": "ragged_greyed"}],
                              "place_state": "the front door forced open, dust on every sill"})
    assert s.looks[0].look == "ragged_greyed" and s.place_state.startswith("the front door")


def test_the_writers_draft_schema_has_no_open_dict_for_looks():
    schema = str(Draft.model_json_schema())
    assert "LookPick" in schema and "place_state" in schema
