"""A character wears one look at a time.  Intervals are (chapter, scene?) so a
chapter can change look between scenes (WotW ch26: ragged in scene 1, the
borrowed suit after), and one look may come back for a second interval."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from studio.continuity_spec import CharacterLooks


def looks() -> dict:
    return {"suit": {"made_by": "base"}, "ragged": {"made_by": "fresh"}, "borrowed": {"made_by": "edit"}}


def card(timeline: list[dict]) -> dict:
    return {"base": "suit", "body": "Man of 34.", "looks": looks(), "timeline": timeline}


def test_two_spans_that_overlap_are_refused():
    with pytest.raises(ValidationError, match="overlap"):
        CharacterLooks.model_validate(card([
            {"look": "suit", "start": {"chapter": 1}, "until": {"chapter": 10}},
            {"look": "ragged", "start": {"chapter": 9}}]))


def test_a_span_that_ends_before_it_starts_is_refused():
    with pytest.raises(ValidationError, match="ends before"):
        CharacterLooks.model_validate(card([
            {"look": "suit", "start": {"chapter": 5}, "until": {"chapter": 4}}]))


def test_a_span_naming_an_undefined_look_is_refused():
    with pytest.raises(ValidationError, match="not defined"):
        CharacterLooks.model_validate(card([{"look": "toga", "start": {"chapter": 1}}]))


def test_a_chapter_can_change_look_between_scenes():
    c = CharacterLooks.model_validate(card([
        {"look": "suit", "start": {"chapter": 1}},
        {"look": "ragged", "start": {"chapter": 22}, "until": {"chapter": 26, "scene": 1}},
        {"look": "borrowed", "start": {"chapter": 26, "scene": 2}}]))
    assert c.look_id_at(26, 1) == "ragged"
    assert c.look_id_at(26, 2) == "borrowed"
    assert c.look_id_at(26) == "ragged"          # a chapter's default is its opening look


def test_a_look_may_return_for_a_second_interval():
    c = CharacterLooks.model_validate(card([
        {"look": "suit", "start": {"chapter": 1}, "until": {"chapter": 6}},
        {"look": "ragged", "start": {"chapter": 7}, "until": {"chapter": 7}},
        {"look": "suit", "start": {"chapter": 8}}]))
    assert [c.look_id_at(n) for n in (6, 7, 8)] == ["suit", "ragged", "suit"]


def test_before_the_first_span_the_base_look_holds():
    c = CharacterLooks.model_validate(card([{"look": "ragged", "start": {"chapter": 22}}]))
    assert c.look_id_at(3) == "suit"


def test_the_looks_a_chapter_allows_are_every_span_meeting_it():
    c = CharacterLooks.model_validate(card([
        {"look": "suit", "start": {"chapter": 1}},
        {"look": "ragged", "start": {"chapter": 22}, "until": {"chapter": 26, "scene": 1}},
        {"look": "borrowed", "start": {"chapter": 26, "scene": 2}}]))
    assert c.allowed_in(26) == ["ragged", "borrowed"]
    assert c.allowed_in(23) == ["ragged"]
