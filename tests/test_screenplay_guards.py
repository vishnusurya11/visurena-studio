"""Step 05's four guards. Deterministic, free, gating — and agent-free to test.

G4 is the interesting one: a failed grounding DOWNGRADES the claim and counts. It never
fails the build, because the line is fine — only its label was wrong.
"""

from __future__ import annotations

from scripts.screenplay import step_05_verify as s05
from studio.screenplay_spec import Issue, Scene, SceneRef, ScriptElement, Slug

SLUG = Slug(int_ext="INT", location_id="221b", location_name="221B Baker Street",
            time="DAY", text="INT. 221B BAKER STREET - DAY")


def _scene(**over):
    base = dict(number=1, beat_id="b1", slug=SLUG,
                source=[SceneRef(chapter=1, scene=1)], speaking=["holmes"])
    return Scene(**{**base, **over})


# --- G1 coordinates ----------------------------------------------------------------

def test_g1_passes_a_real_coordinate():
    assert s05.g1_coordinates(_scene(), {(1, 1)}) == []


def test_g1_catches_an_invented_coordinate():
    assert s05.g1_coordinates(_scene(), {(2, 2)}) != []


def test_g1_reports_the_offending_pair():
    problems = s05.g1_coordinates(_scene(), set())
    assert "(1, 1)" in problems[0]


# --- G2 roster ---------------------------------------------------------------------

def test_g2_passes_a_character_the_source_places_there():
    assert s05.g2_roster(_scene(), {"holmes"}, {1: {"holmes"}}) == []


def test_g2_catches_a_character_absent_from_the_registry():
    assert any("registry" in p for p in s05.g2_roster(_scene(), set(), {1: {"holmes"}}))


def test_g2_catches_a_speaker_the_timeline_puts_elsewhere():
    """Bilocation. He exists, he is just not in this room."""
    problems = s05.g2_roster(_scene(), {"holmes"}, {1: {"watson"}})
    assert any("do not place them" in p for p in problems)


# --- G3 place and time -------------------------------------------------------------

def test_g3_allows_narrowing_day_to_dawn():
    scene = _scene(slug=SLUG.model_copy(update={"time": "DAWN"}))
    source = {"chapter": 1, "scene": 1, "time_of_day": "DAY", "location_id": "221b"}
    assert s05.g3_place_and_time(scene, [source]) == []


def test_g3_refuses_day_to_night():
    scene = _scene(slug=SLUG.model_copy(update={"time": "NIGHT"}))
    source = {"chapter": 1, "scene": 1, "time_of_day": "DAY", "location_id": "221b"}
    assert any("slug says NIGHT" in p for p in s05.g3_place_and_time(scene, [source]))


def test_g3_allows_continuous_under_either_source_time():
    for source_time in ("DAY", "NIGHT"):
        scene = _scene(slug=SLUG.model_copy(update={"time": "CONTINUOUS"}))
        source = {"chapter": 1, "scene": 1, "time_of_day": source_time,
                  "location_id": "221b"}
        assert s05.g3_place_and_time(scene, [source]) == []


def test_g3_catches_a_moved_location():
    source = {"chapter": 1, "scene": 1, "time_of_day": "DAY", "location_id": "lauriston"}
    assert any("slug at" in p for p in s05.g3_place_and_time(_scene(), [source]))


def test_g3_stays_silent_when_the_source_has_no_time():
    source = {"chapter": 1, "scene": 1, "time_of_day": None, "location_id": "221b"}
    assert s05.g3_place_and_time(_scene(), [source]) == []


# --- G4 verbatim -------------------------------------------------------------------

def test_g4_passes_a_line_that_is_really_in_the_source():
    scene = _scene(elements=[ScriptElement(
        kind="dialogue", text="I have found it", character="holmes",
        provenance="verbatim", source=SceneRef(chapter=1, scene=1))])
    assert s05.g4_verbatim(scene, {"1:1": ["He cried, I have found it, at last."]}) == []


def test_g4_downgrades_an_unfounded_verbatim_claim():
    scene = _scene(elements=[ScriptElement(
        kind="dialogue", text="Elementary, my dear Watson", character="holmes",
        provenance="verbatim", source=SceneRef(chapter=1, scene=1))])
    problems = s05.g4_verbatim(scene, {"1:1": ["He said nothing of the kind."]})
    assert problems and scene.elements[0].provenance == "adapted"


def test_g4_leaves_adapted_and_invented_lines_alone():
    scene = _scene(elements=[
        ScriptElement(kind="dialogue", text="x", character="holmes",
                      provenance="adapted"),
        ScriptElement(kind="action", text="y", provenance="invented")])
    assert s05.g4_verbatim(scene, {"1:1": ["nothing"]}) == []


# --- the sample and the evidence gate ----------------------------------------------

def test_sample_takes_first_middle_last():
    scenes = list(range(9))
    assert s05.sample(scenes, 3) == [0, 4, 8]


def test_sample_returns_everything_when_there_is_little():
    assert s05.sample([1, 2], 3) == [1, 2]


def _issue(quote):
    return Issue(scene=1, kind="place", severity="blocking", book_quote=quote,
                 script_quote="x", why="y")


def test_an_issue_quoting_the_source_survives():
    kept = s05.keep_grounded_issues([_issue("he was in London")],
                                    ["At that time he was in London."])
    assert len(kept) == 1


def test_an_issue_whose_quote_is_not_in_the_source_is_dropped():
    """The auditor cannot manufacture evidence. Dropped BEFORE the improve loop, so a
    hallucinated finding never costs a paid re-run."""
    kept = s05.keep_grounded_issues([_issue("he was in Vienna")],
                                    ["At that time he was in London."])
    assert kept == []
