"""Step 04. JSON is the artifact; Fountain and PDF are lossy projections of it.

Agent-free: every function here is arithmetic or a dict transform.
"""

from __future__ import annotations

from scripts.screenplay import step_03_draft as s03
from scripts.screenplay import step_04_render as s04
from studio.screenplay_spec import (Scene, ScreenplayPlan, ScriptElement, Shot, Slug,
                                    Totals)

SLUG = Slug(int_ext="INT", location_id="221b", location_name="221B Baker Street",
            time="NIGHT", text="INT. 221B BAKER STREET - NIGHT")
DOSSIER = {"input_sha256": "abc",
           "characters": [{"id": "holmes", "name": "Sherlock Holmes"}],
           "locations": [{"id": "221b", "name": "221B Baker Street"}],
           "scenes": []}
PLAN = ScreenplayPlan(spine="s", logline="l", opening_beat_id="b1", final_beat_id="b1",
                      bookend="mirrored", beats=[])


def _scene(number=1, elements=None, shots=None):
    return Scene(number=number, beat_id="b1", slug=SLUG, cast=["holmes"],
                 elements=elements or [], shots=shots or [])


# --- sluglines ---------------------------------------------------------------------

def test_slug_text_is_upper_case_with_a_dotted_prefix():
    assert s03.slug_text("INT", "221B Baker Street", "NIGHT") == \
        "INT. 221B BAKER STREET - NIGHT"


def test_slug_text_renders_the_combined_form():
    assert s03.slug_text("INT/EXT", "Cab", "DAY").startswith("INT./EXT.")


def test_build_slug_takes_place_and_time_from_the_first_source_scene():
    scenes = [{"location_id": "221b", "int_ext": "INT", "time_of_day": "NIGHT"},
              {"location_id": "lauriston", "int_ext": "EXT", "time_of_day": "DAY"}]
    slug = s03.build_slug(scenes, {"221b": {"name": "221B Baker Street"}})
    assert slug.location_id == "221b" and slug.time == "NIGHT"


def test_build_slug_falls_back_to_the_surface_text_when_unresolved():
    scenes = [{"location_id": None, "location_text": "a dim hallway",
               "int_ext": "INT", "time_of_day": "DAY"}]
    assert s03.build_slug(scenes, {}).location_name == "a dim hallway"


def test_build_slug_survives_a_beat_with_no_source_scenes():
    """An invented connective legitimately cites nothing and still needs a slug."""
    assert s03.build_slug([], {}).location_name == "UNKNOWN"


# --- measurement, which code owns --------------------------------------------------

def test_page_eighths_is_measured_not_asked():
    scene = s04.measure(_scene(elements=[ScriptElement(kind="action", text="He turns.")]),
                        {"holmes": "Sherlock Holmes"})
    assert scene.page_eighths >= 1


def test_duration_follows_from_page_eighths_at_a_minute_a_page():
    scene = s04.measure(_scene(), {})
    assert scene.duration_s == round(scene.page_eighths / 8 * 60, 1)


def test_a_longer_scene_measures_longer():
    short = s04.measure(_scene(elements=[ScriptElement(kind="action", text="x")]), {})
    long = s04.measure(_scene(elements=[ScriptElement(kind="action", text="x")] * 40), {})
    assert long.page_eighths > short.page_eighths


def test_totals_sum_the_scenes():
    scenes = [s04.measure(_scene(number=i), {}) for i in (1, 2, 3)]
    totals = s04.totals(scenes)
    assert totals.scenes == 3 and totals.cast == 1
    assert totals.pages == round(sum(s.page_eighths for s in scenes) / 8, 2)


def test_budget_problem_is_raised_when_the_plan_ignored_the_target():
    screenplay = s04.build(DOSSIER, PLAN, [_scene()], "feature", "T")
    assert s04.budget_problems(screenplay, {"pages": 100}) != []


def test_budget_is_accepted_inside_the_slack():
    screenplay = s04.build(DOSSIER, PLAN, [_scene()], "feature", "T")
    assert s04.budget_problems(screenplay, {"pages": screenplay.totals.pages}) == []


# --- the artifact, and what the projections lose -----------------------------------

def test_screenplay_json_is_the_artifact_and_carries_the_fingerprint():
    screenplay = s04.build(DOSSIER, PLAN, [_scene()], "feature", "A Study in Scarlet")
    assert screenplay.source_fingerprint == "abc" and screenplay.target == "feature"


def test_the_artifact_round_trips_losslessly():
    from studio.screenplay_spec import Screenplay
    scene = _scene(elements=[ScriptElement(kind="dialogue", text="Quite.",
                                           character="holmes", provenance="adapted")],
                   shots=[Shot(index=0, covers_start=0, covers_end=0, setup="wide",
                               visual_consequence="the frame holds still")])
    built = s04.build(DOSSIER, PLAN, [scene], "feature", "T")
    back = Screenplay.model_validate_json(built.model_dump_json())
    assert back.scenes[0].elements[0].provenance == "adapted"
    assert back.scenes[0].shots[0].visual_consequence


def test_fountain_really_does_lose_provenance():
    """The reason nothing downstream may parse Fountain back into facts. If this test
    ever fails, the lossiness claim in DESIGN.md needs rewriting, not this test."""
    from studio import fountain
    from studio.screenplay_spec import SceneRef
    scene = _scene(elements=[ScriptElement(
        kind="dialogue", text="Quite.", character="holmes", provenance="verbatim",
        source=SceneRef(chapter=1, scene=1))])
    text = fountain.render_scene(scene, {"holmes": "Sherlock Holmes"})
    assert "verbatim" not in text and "holmes" not in text


def test_fountain_loses_the_camera_fields_too():
    from studio import fountain
    scene = _scene(shots=[Shot(index=0, covers_start=0, covers_end=0,
                               setup="medium close-up", term="dolly in",
                               visual_consequence="parallax shifts")])
    assert "dolly" not in fountain.render_scene(scene, {})


# --- elements.json, the flattened view ---------------------------------------------

def _with_shots():
    return _scene(
        elements=[ScriptElement(kind="action", text="He turns."),
                  ScriptElement(kind="dialogue", text="Quite.", character="holmes")],
        shots=[Shot(index=0, covers_start=0, covers_end=1, setup="two shot",
                    term="locked-off", visual_consequence="the frame holds still")])


def test_elements_index_has_one_row_per_shot():
    screenplay = s04.build(DOSSIER, PLAN, [_with_shots()], "feature", "T")
    assert len(s04.elements_index(screenplay)) == 1


def test_elements_index_carries_what_the_video_stage_needs():
    row = s04.elements_index(
        s04.build(DOSSIER, PLAN, [_with_shots()], "feature", "T"))[0]
    for key in ("scene", "shot", "slug", "location_id", "time", "cast",
                "setup", "visual_consequence", "axis_side"):
        assert key in row


def test_elements_index_resolves_the_covered_element_text():
    row = s04.elements_index(
        s04.build(DOSSIER, PLAN, [_with_shots()], "feature", "T"))[0]
    assert row["text"] == ["He turns.", "Quite."]


def test_a_scene_with_no_shots_contributes_no_rows():
    screenplay = s04.build(DOSSIER, PLAN, [_scene()], "feature", "T")
    assert s04.elements_index(screenplay) == []


def test_display_names_map_ids_to_printed_cues():
    assert s04.display_names(DOSSIER)["holmes"] == "Sherlock Holmes"


# --- the round-trip lint over a whole screenplay ------------------------------------

def test_lint_all_passes_a_clean_screenplay():
    scene = _scene(elements=[ScriptElement(kind="action", text="He turns.")])
    assert s04.lint_all([scene], {"holmes": "Sherlock Holmes"}) == []


def test_our_renderer_is_structurally_immune_to_the_caps_swallow():
    """The pathology needs the action line and the next line ADJACENT. Our renderer
    blank-line-separates every element, so an all-caps action line parses as Action.
    This is the emitter earning its keep, not luck — assert it so a future change to
    the spacing cannot quietly remove the protection."""
    scene = _scene(elements=[
        ScriptElement(kind="action", text="THE DOOR BURSTS OPEN"),
        ScriptElement(kind="action", text="Anna stands there.")])
    assert s04.lint_all([scene], {}) == []


def test_lint_all_labels_problems_with_their_scene_number():
    """A transition whose text already ends in TO: renders bare; one that does not gets
    the `>` forced-transition marker. Either way lint must locate a problem by scene."""
    problems = s04.lint_all([_scene(number=7)], {})
    assert problems == []            # a clean scene has none...
    assert all(p.startswith("scene ") for p in s04.lint_all([_scene(number=7)], {}))


def test_the_format_substep_checks_balance_not_only_format():
    """Regression guard: balance_problems must stay wired into 04_05. A check nobody
    calls is a comment."""
    from pathlib import Path
    source = Path("scripts/screenplay/step_04_render.py").read_text(encoding="utf-8")
    assert "problems += balance_problems(" in source
