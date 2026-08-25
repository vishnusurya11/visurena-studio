"""Screenplay step 01 — the join.

Analysis scattered one scene's facts across three artifacts, because each was written
by a different step for a different reason. The screenplay needs them in one record.

The reason this step reads timeline.json rather than scenes.json is load-bearing:
scenes.json leaves 27 of this book's 92 scenes at UNKNOWN location, because it predates
the timeline solver's gap filling. int_ext, dialogue, events and pov survive ONLY in
analysis/extraction/, which the timeline never carried forward. Neither file alone can
produce a slugline.
"""

from __future__ import annotations

import pytest

from scripts.screenplay import step_01_dossier as s01

REGISTRY = {
    "characters": [
        {"id": "john_watson", "name": "Dr. John Watson", "aliases": ["I", "Watson"]},
        {"id": "sherlock_holmes", "name": "Sherlock Holmes", "aliases": ["my companion"]},
    ],
    "locations": [
        {"id": "221b_baker_street", "name": "221B Baker Street", "aliases": ["the rooms"]},
    ],
}

TIMELINE_SCENE = {
    "chapter": 2, "scene": 1, "type": "scene",
    "location_id": "221b_baker_street", "location_text": "the rooms",
    "characters": ["john_watson", "sherlock_holmes"],
    "time_of_day": "DAY", "story_day": 3, "t": 12.0,
    "para_start": 4, "para_end": 9, "summary": "They inspect the rooms.",
}

EXTRACTION_SCENE = {
    "n": 1, "para_start": 4, "para_end": 9, "type": "scene",
    "int_ext": "Interior", "location_text": "the rooms", "time_of_day": "DAY",
    "characters": [{"name_text": "I", "presence": "present", "role": "agent"},
                   {"name_text": "my companion", "presence": "present", "role": "agent"}],
    "dialogue": [{"speaker_text": "my companion", "addressee_text": "Watson",
                  "attribution": "explicit", "para": 6,
                  "notable_quote": "You have been in Afghanistan."}],
    "events": [{"type": "action", "summary": "They agree to share rooms."}],
}

# pov is a dict per chapter, exactly as analysis writes it — not a bare name.
EXTRACTION = {"chapter": 2,
              "pov": {"narrator": "Dr. John Watson, first person", "tense": "past"},
              "scenes": [EXTRACTION_SCENE]}


# --- the join ----------------------------------------------------------------------

def test_join_attaches_int_ext_from_extraction():
    """int_ext exists ONLY in extraction; the timeline dropped it."""
    scenes = s01.join([TIMELINE_SCENE], {2: EXTRACTION}, REGISTRY)
    assert scenes[0]["int_ext"] == "INT"


def test_join_attaches_dialogue_and_events():
    scenes = s01.join([TIMELINE_SCENE], {2: EXTRACTION}, REGISTRY)
    assert len(scenes[0]["dialogue"]) == 1 and len(scenes[0]["events"]) == 1


def test_join_carries_pov_from_the_chapter_not_the_scene():
    """pov is recorded once per chapter in extraction, never per scene."""
    scenes = s01.join([TIMELINE_SCENE], {2: EXTRACTION}, REGISTRY)
    assert scenes[0]["pov"] == "john_watson"


def test_dialogue_speaker_resolves_to_a_canonical_id():
    scenes = s01.join([TIMELINE_SCENE], {2: EXTRACTION}, REGISTRY)
    assert scenes[0]["dialogue"][0]["speaker_id"] == "sherlock_holmes"


def test_speaking_is_a_subset_of_cast():
    scenes = s01.join([TIMELINE_SCENE], {2: EXTRACTION}, REGISTRY)
    scene = scenes[0]
    assert scene["speaking"] == ["sherlock_holmes"]
    assert set(scene["speaking"]) <= set(scene["cast"])


def test_unresolvable_speaker_keeps_the_surface_form_and_a_null_id():
    """A walk-on has no canonical identity. Losing the line is worse than a null."""
    extraction = {**EXTRACTION, "scenes": [{**EXTRACTION_SCENE, "dialogue": [
        {"speaker_text": "a railway porter", "notable_quote": "Mind the step."}]}]}
    scenes = s01.join([TIMELINE_SCENE], {2: extraction}, REGISTRY)
    line = scenes[0]["dialogue"][0]
    assert line["speaker_id"] is None and line["speaker_text"] == "a railway porter"


def test_scene_with_no_matching_extraction_still_joins():
    """Never drop a scene because a sibling artifact is thin — that is silent loss."""
    scenes = s01.join([TIMELINE_SCENE], {}, REGISTRY)
    assert len(scenes) == 1 and scenes[0]["int_ext"] == "UNKNOWN"


def test_join_preserves_paragraph_span_for_grounding():
    scenes = s01.join([TIMELINE_SCENE], {2: EXTRACTION}, REGISTRY)
    assert (scenes[0]["para_start"], scenes[0]["para_end"]) == (4, 9)


def test_extraction_scenes_match_by_number_not_position():
    """Scene n is the identity. Position in the list is not, and assuming it silently
    attaches one scene's dialogue to another."""
    extraction = {"chapter": 2, "pov": None, "scenes": [
        {**EXTRACTION_SCENE, "n": 7, "int_ext": "Exterior", "dialogue": []},
        EXTRACTION_SCENE,
    ]}
    scenes = s01.join([TIMELINE_SCENE], {2: extraction}, REGISTRY)
    assert scenes[0]["int_ext"] == "INT"


# --- the checks --------------------------------------------------------------------

def test_check_passes_a_complete_scene():
    scenes = s01.join([TIMELINE_SCENE], {2: EXTRACTION}, REGISTRY)
    problems, _ = s01.check(scenes, profiles={"sherlock_holmes": {"voice": "clipped"}})
    assert problems == []


def test_check_flags_a_missing_time_of_day():
    scene = {**TIMELINE_SCENE, "time_of_day": None}
    scenes = s01.join([scene], {2: EXTRACTION}, REGISTRY)
    problems, _ = s01.check(scenes, profiles={})
    assert any("time" in p for p in problems)


def test_check_flags_a_missing_location():
    scene = {**TIMELINE_SCENE, "location_id": None, "location_text": ""}
    scenes = s01.join([scene], {2: EXTRACTION}, REGISTRY)
    problems, _ = s01.check(scenes, profiles={})
    assert any("location" in p for p in problems)


def test_missing_voice_profile_warns_but_never_fails():
    """15 of this book's 23 speaking characters have no voice profile today. That is a
    quality signal for the screenwriter, not a reason to refuse to build."""
    scenes = s01.join([TIMELINE_SCENE], {2: EXTRACTION}, REGISTRY)
    problems, warnings = s01.check(scenes, profiles={})
    assert problems == []
    assert any("sherlock_holmes" in w for w in warnings)


def test_unknown_int_ext_is_a_warning_not_a_problem():
    scenes = s01.join([TIMELINE_SCENE], {}, REGISTRY)
    problems, warnings = s01.check(scenes, profiles={})
    assert problems == []
    assert any("int_ext" in w for w in warnings)

# --- shapes taken from the real artifacts, not invented ----------------------------

def test_pov_is_read_out_of_the_narrator_field():
    """analysis writes pov as {"narrator": ..., "tense": ...}. Handing the dict to the
    matcher raised AttributeError on the first real run — fixtures had drifted."""
    scenes = s01.join([TIMELINE_SCENE], {2: EXTRACTION}, REGISTRY)
    assert scenes[0]["pov"] == "john_watson"


def test_narration_tense_is_carried_for_the_screenwriter():
    scenes = s01.join([TIMELINE_SCENE], {2: EXTRACTION}, REGISTRY)
    assert scenes[0]["narration"]["tense"] == "past"


def test_missing_pov_block_resolves_to_none():
    extraction = {**EXTRACTION, "pov": None}
    scenes = s01.join([TIMELINE_SCENE], {2: extraction}, REGISTRY)
    assert scenes[0]["pov"] is None


def test_addressee_resolves_to_a_canonical_id_too():
    """Who a line is aimed at is what makes it a tactic rather than a statement."""
    scenes = s01.join([TIMELINE_SCENE], {2: EXTRACTION}, REGISTRY)
    assert scenes[0]["dialogue"][0]["addressee_id"] == "john_watson"


def test_quote_and_paragraph_survive_for_grounding():
    scenes = s01.join([TIMELINE_SCENE], {2: EXTRACTION}, REGISTRY)
    line = scenes[0]["dialogue"][0]
    assert line["notable_quote"].startswith("You have been") and line["para"] == 6


def test_bare_surname_speaker_resolves_through_the_fallback():
    """'Watson' is not among the registry's aliases for Dr. John Watson. On the first
    real run that cost 17 of his lines their speaker."""
    extraction = {**EXTRACTION, "scenes": [{**EXTRACTION_SCENE, "dialogue": [
        {"speaker_text": "Watson", "notable_quote": "You seem very happy."}]}]}
    scenes = s01.join([TIMELINE_SCENE], {2: extraction}, REGISTRY)
    assert scenes[0]["dialogue"][0]["speaker_id"] == "john_watson"


def test_the_alias_index_still_wins_over_the_surname_fallback():
    """'my companion' is an alias for Holmes. The fallback must never pre-empt it."""
    scenes = s01.join([TIMELINE_SCENE], {2: EXTRACTION}, REGISTRY)
    assert scenes[0]["dialogue"][0]["speaker_id"] == "sherlock_holmes"


def test_extractor_sentinels_stay_unresolved():
    """'_unknowable' and '_group' are the extractor saying it could not tell. Inventing
    a speaker for them would be worse than the gap."""
    extraction = {**EXTRACTION, "scenes": [{**EXTRACTION_SCENE, "dialogue": [
        {"speaker_text": "_unknowable", "notable_quote": "Move along."},
        {"speaker_text": "_group", "notable_quote": "Hear, hear."}]}]}
    scenes = s01.join([TIMELINE_SCENE], {2: extraction}, REGISTRY)
    assert all(line["speaker_id"] is None for line in scenes[0]["dialogue"])
