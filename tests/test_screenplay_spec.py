"""The contracts. Pure pydantic — no agents, no network, no files, no spend.

The pydantic contract IS the spec, so these tests are the spec's own test suite: if a
field can hold a value the pipeline cannot process, that is a defect in the contract,
not in the code that later trips over it.
"""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from studio.screenplay_spec import (AuditVerdict, Beat, Issue, Omission, Scene,
                                    SceneDraft, SceneRef, Screenplay, ScreenplayPlan,
                                    ScriptElement, Shot, ShotPlan, Slug, Totals)

AGENT_SCHEMAS = [SceneDraft, ScreenplayPlan, ShotPlan, AuditVerdict]


# --- the provider-safety rule that cost us 800 calls once --------------------------

@pytest.mark.parametrize("model", AGENT_SCHEMAS, ids=lambda m: m.__name__)
def test_element_schema_is_provider_safe(model):
    """studio/llm.py uses strict structured outputs. Pydantic emits tagged unions as
    oneOf + discriminator, which the provider rejects. Flip to a union, run this, keep
    it only if it passes."""
    schema = json.dumps(model.model_json_schema())
    assert "oneOf" not in schema and "discriminator" not in schema


@pytest.mark.parametrize("model", AGENT_SCHEMAS, ids=lambda m: m.__name__)
def test_agent_schema_round_trips_through_json(model):
    assert model.model_validate_json(
        json.dumps(model.model_json_schema() and _example(model))) is not None


def _example(model):
    return {
        SceneDraft: {"elements": []},
        ShotPlan: {"shots": []},
        AuditVerdict: {"ok": True, "issues": []},
        ScreenplayPlan: {"spine": "s", "logline": "l", "opening_beat_id": "b1",
                         "final_beat_id": "b1", "bookend": "x", "beats": []},
    }[model]


# --- ScriptElement -----------------------------------------------------------------

def test_element_defaults_to_invented():
    """The safe default. A line is not the book's words unless someone says so."""
    assert ScriptElement(kind="action", text="He turns.").provenance == "invented"


def test_element_rejects_an_unknown_kind():
    with pytest.raises(ValidationError):
        ScriptElement(kind="song", text="la")


def test_element_rejects_an_unknown_provenance():
    with pytest.raises(ValidationError):
        ScriptElement(kind="action", text="x", provenance="probably")


def test_dialogue_may_carry_a_parenthetical():
    element = ScriptElement(kind="dialogue", text="Never mind.",
                            character="holmes", parenthetical="beat")
    assert element.parenthetical == "beat"


def test_verbatim_element_can_carry_its_source_ref():
    element = ScriptElement(kind="dialogue", text="Quite.", character="watson",
                            provenance="verbatim", source=SceneRef(chapter=2, scene=1))
    assert element.source.chapter == 2


def test_dual_dialogue_defaults_off():
    assert ScriptElement(kind="dialogue", text="x", character="a").dual is False


# --- Beat and the plan -------------------------------------------------------------

def _beat(**over):
    base = dict(id="b1", intent="i", unifying_aspect="u", protagonist="watson",
                objective="to learn the truth", boundary_event="he leaves",
                source=[SceneRef(chapter=1, scene=1)], transfer="transfer")
    return Beat(**{**base, **over})


def test_beat_requires_an_objective_and_a_boundary():
    with pytest.raises(ValidationError):
        Beat(id="b1", intent="i", unifying_aspect="u", protagonist="w",
             source=[], transfer="transfer")


def test_beat_defaults_are_the_conservative_ones():
    beat = _beat()
    assert beat.cold_open is False and beat.flashback is False
    assert beat.reversal is None and beat.difficulty == "easy"


def test_beat_rejects_an_unknown_transfer_class():
    with pytest.raises(ValidationError):
        _beat(transfer="mostly")


def test_beat_accepts_the_three_transfer_classes():
    for value in ("transfer", "adaptation_proper", "invented_connective"):
        assert _beat(transfer=value).transfer == value


def test_invented_connective_needs_no_source_scenes():
    """A bridge the book never staged legitimately cites nothing."""
    assert _beat(transfer="invented_connective", source=[]).source == []


def test_plan_omissions_carry_a_reason():
    omission = Omission(source=SceneRef(chapter=3, scene=2), reason="subplot cut")
    assert omission.reason


def test_omission_without_a_reason_is_rejected():
    """Silent dropping is the failure mode of adaptation, so the contract forbids it."""
    with pytest.raises(ValidationError):
        Omission(source=SceneRef(chapter=3, scene=2))


def test_plan_round_trips_through_json():
    plan = ScreenplayPlan(spine="s", logline="l", opening_beat_id="b1",
                          final_beat_id="b1", bookend="mirrored", beats=[_beat()])
    assert ScreenplayPlan.model_validate_json(plan.model_dump_json()).beats[0].id == "b1"


# --- Shot --------------------------------------------------------------------------

def _shot(**over):
    base = dict(index=0, covers_start=0, covers_end=2, setup="medium close-up on Holmes",
                visual_consequence="the frame holds still")
    return Shot(**{**base, **over})


def test_shot_term_may_be_null_when_no_vocabulary_fits():
    """An honest null beats a coined word no downstream system recognises."""
    assert _shot().term is None


def test_shot_always_carries_a_visual_consequence():
    with pytest.raises(ValidationError):
        Shot(index=0, covers_start=0, covers_end=1, setup="wide")


def test_shot_defaults_to_not_crossing_the_axis():
    shot = _shot()
    assert shot.crosses_axis is False and shot.licensed_by is None


def test_shot_rejects_an_axis_side_outside_a_and_b():
    with pytest.raises(ValidationError):
        _shot(axis_side="C")


def test_shot_travel_direction_is_left_or_right_only():
    with pytest.raises(ValidationError):
        _shot(travel_direction="forward")


# --- Slug and Scene ----------------------------------------------------------------

def _slug(**over):
    base = dict(int_ext="INT", location_id="221b", location_name="221B Baker Street",
                time="NIGHT", text="INT. 221B BAKER STREET - NIGHT")
    return Slug(**{**base, **over})


def test_slug_accepts_the_observed_int_ext_values():
    for value in ("INT", "EXT", "INT/EXT", "UNKNOWN"):
        assert _slug(int_ext=value).int_ext == value


def test_slug_rejects_a_free_text_int_ext():
    with pytest.raises(ValidationError):
        _slug(int_ext="Interior")


def test_slug_rejects_an_unknown_time_of_day():
    """UNKNOWN is deliberately NOT a legal slug time — a slugline must state one."""
    with pytest.raises(ValidationError):
        _slug(time="UNKNOWN")


def test_slug_accepts_the_continuity_times():
    for value in ("CONTINUOUS", "LATER", "MOMENTS LATER"):
        assert _slug(time=value).time == value


def test_slug_location_id_may_be_null_but_the_name_may_not():
    assert _slug(location_id=None).location_id is None
    with pytest.raises(ValidationError):
        Slug(int_ext="INT", location_id="x", time="DAY", text="t")


def test_scene_measurements_default_to_zero_until_code_measures_them():
    """page_eighths and duration are MEASURED after rendering, never asked of an agent."""
    scene = Scene(number=1, beat_id="b1", slug=_slug())
    assert scene.page_eighths == 0 and scene.duration_s == 0.0


def test_scene_collections_default_empty_not_none():
    """Callers iterate these without guarding. None would be a crash per field."""
    scene = Scene(number=1, beat_id="b1", slug=_slug())
    for field in ("cast", "speaking", "elements", "shots", "source"):
        assert getattr(scene, field) == []


def test_scene_round_trips_with_elements_and_shots():
    scene = Scene(number=1, beat_id="b1", slug=_slug(),
                  elements=[ScriptElement(kind="action", text="He turns.")],
                  shots=[_shot()])
    back = Scene.model_validate_json(scene.model_dump_json())
    assert back.elements[0].text == "He turns." and back.shots[0].covers_end == 2


# --- Issue and the audit verdict ---------------------------------------------------

def _issue(**over):
    base = dict(scene=1, kind="place", severity="blocking",
                book_quote="he was in London", script_quote="INT. PARIS",
                why="the book puts him in London")
    return Issue(**{**base, **over})


def test_issue_requires_a_book_quote():
    """No quote, no issue. The contract enforces it before the grounding check does."""
    with pytest.raises(ValidationError):
        Issue(scene=1, kind="place", severity="blocking",
              script_quote="x", why="feels wrong")


def test_issue_kinds_are_the_seven_contradiction_types():
    for kind in ("place", "knowledge", "deduction", "state", "identity",
                 "verbatim", "period"):
        assert _issue(kind=kind).kind == kind


def test_issue_rejects_a_quality_judgement_as_a_kind():
    """'tone' and 'pacing' are not contradictions and must not be reportable."""
    for kind in ("tone", "pacing", "quality"):
        with pytest.raises(ValidationError):
            _issue(kind=kind)


def test_verdict_defaults_to_an_empty_issue_list():
    assert AuditVerdict(ok=True).issues == []


def test_totals_round_trip():
    totals = Totals(scenes=20, pages=98.5, runtime_s=5910.0, cast=12)
    assert Totals.model_validate_json(totals.model_dump_json()).pages == 98.5


def test_screenplay_requires_a_fingerprint_of_its_inputs():
    """Without it nothing can invalidate the target when analysis changes upstream."""
    with pytest.raises(ValidationError):
        Screenplay(title="t", source_work="t", target="feature",
                   totals=Totals(scenes=0, pages=0, runtime_s=0, cast=0))


# --- validators that stop garbage reaching the page --------------------------------

def test_dialogue_without_a_character_is_rejected():
    """It rendered a headless cue — ' (CONT'D)' with no name — and the parser was
    perfectly happy with it. Caught at the contract now, not three steps downstream."""
    with pytest.raises(ValidationError):
        ScriptElement(kind="dialogue", text="Quite.")


def test_action_may_not_carry_a_parenthetical():
    with pytest.raises(ValidationError):
        ScriptElement(kind="action", text="He turns.", parenthetical="beat")


def test_verbatim_without_a_source_is_rejected():
    """The one label that must never be taken on trust."""
    with pytest.raises(ValidationError):
        ScriptElement(kind="dialogue", text="x", character="a", provenance="verbatim")


def test_verbatim_with_a_source_is_accepted():
    element = ScriptElement(kind="dialogue", text="x", character="a",
                            provenance="verbatim", source=SceneRef(chapter=1, scene=1))
    assert element.provenance == "verbatim"


def test_adapted_needs_no_source():
    assert ScriptElement(kind="dialogue", text="x", character="a",
                         provenance="adapted").source is None


# --- emotion on dialogue (2026-08-28) ----------------------------------------------
#
# Owner asked for it, and it belongs on the DATA rather than in the text: a downstream
# voice, an actor's sides, and a shot's mood all want it, and none of them should have
# to parse it back out of a parenthetical.
#
# It is deliberately NOT a parenthetical. Parentheticals are timing notes and are rare in
# professional practice (0.81 per page, commonest is "(beat)"); an emotion adverb in one
# is the classic amateur tell. This keeps the information and keeps it off the page.

def test_dialogue_may_carry_an_emotion():
    element = ScriptElement(kind="dialogue", text="Quite.", character="holmes",
                            emotion="dry")
    assert element.emotion == "dry"


def test_emotion_defaults_to_none_rather_than_neutral():
    """A missing emotion is 'nobody said', not 'the actor should play it flat'."""
    assert ScriptElement(kind="dialogue", text="x", character="a").emotion is None


def test_action_may_not_carry_an_emotion():
    """Emotion belongs to a speaker. An action line has no one to feel it."""
    with pytest.raises(ValidationError):
        ScriptElement(kind="action", text="He turns.", emotion="angry")


def test_an_action_may_not_carry_a_character():
    """Found in the shipped screenplay.json: an action line with
    character='john_watson'. It is not a cue, it leaks into cast lists and shot rows,
    and nothing downstream can tell it from a real speaker."""
    with pytest.raises(ValidationError):
        ScriptElement(kind="action", text="Watson sits.", character="john_watson")


def test_a_transition_may_not_carry_a_character():
    with pytest.raises(ValidationError):
        ScriptElement(kind="transition", text="CUT TO:", character="holmes")


def test_dialogue_still_requires_its_character():
    with pytest.raises(ValidationError):
        ScriptElement(kind="dialogue", text="Quite.")
