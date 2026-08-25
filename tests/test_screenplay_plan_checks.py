"""Step 02's checks. Pure functions over a plan object — no agent, no network.

These are the checks that make an LLM plan trustworthy, so they are the ones most worth
testing: the agent is told the budget, and CODE measures the result.
"""

from __future__ import annotations

from scripts.screenplay import step_02_plan as s02
from studio.screenplay_spec import Beat, Omission, ScreenplayPlan, SceneRef

TARGET = {"pages": 100, "beats": [1, 4], "style": "x"}

DOSSIER = {
    "scenes": [{"chapter": 1, "scene": 1}, {"chapter": 1, "scene": 2},
               {"chapter": 2, "scene": 1}],
    "characters": [{"id": "watson", "name": "Dr. John Watson"},
                   {"id": "holmes", "name": "Sherlock Holmes"}],
    "locations": [{"id": "221b", "name": "221B Baker Street"}],
}


def _beat(bid="b1", refs=((1, 1),), protagonist="watson", reversal="he is wrong"):
    return Beat(id=bid, intent="i", unifying_aspect="u", protagonist=protagonist,
                objective="to know", boundary_event="he leaves",
                source=[SceneRef(chapter=c, scene=s) for c, s in refs],
                transfer="transfer", reversal=reversal)


def _plan(beats=None, omitted=None, **over):
    beats = beats if beats is not None else [_beat(refs=((1, 1), (1, 2), (2, 1)))]
    base = dict(spine="s", logline="l", opening_beat_id=beats[0].id,
                final_beat_id=beats[-1].id, bookend="mirrored",
                beats=beats, omitted=omitted or [])
    return ScreenplayPlan(**{**base, **over})


def test_a_complete_plan_has_no_problems():
    assert s02.check(_plan(), DOSSIER, TARGET) == []


def test_a_beat_citing_a_nonexistent_scene_is_caught():
    plan = _plan([_beat(refs=((9, 9),))], omitted=[
        Omission(source=SceneRef(chapter=c, scene=s), reason="cut")
        for c, s in ((1, 1), (1, 2), (2, 1))])
    assert any("does not exist" in p for p in s02.check(plan, DOSSIER, TARGET))


def test_a_protagonist_outside_the_registry_is_caught():
    plan = _plan([_beat(refs=((1, 1), (1, 2), (2, 1)), protagonist="moriarty")])
    assert any("registry" in p for p in s02.check(plan, DOSSIER, TARGET))


def test_a_silently_dropped_scene_is_caught():
    """The whole point of the check: an omission you can defend is fine, an omission
    nobody noticed is not."""
    problems = s02.check(_plan([_beat(refs=((1, 1),))]), DOSSIER, TARGET)
    assert any("silent drop" in p for p in problems)


def test_an_explicitly_omitted_scene_is_accepted():
    plan = _plan([_beat(refs=((1, 1),))], omitted=[
        Omission(source=SceneRef(chapter=1, scene=2), reason="subplot cut"),
        Omission(source=SceneRef(chapter=2, scene=1), reason="merged upward")])
    assert s02.check(plan, DOSSIER, TARGET) == []


def test_too_many_beats_for_the_target_is_caught():
    beats = [_beat(bid=f"b{i}", refs=((1, 1),)) for i in range(6)]
    plan = _plan(beats, omitted=[
        Omission(source=SceneRef(chapter=c, scene=s), reason="cut")
        for c, s in ((1, 2), (2, 1))])
    assert any("outside target window" in p for p in s02.check(plan, DOSSIER, TARGET))


# --- the opening/ending pair -------------------------------------------------------

def test_an_opening_beat_id_that_matches_no_beat_is_caught():
    plan = _plan(opening_beat_id="nope")
    assert any("opening_beat_id" in p for p in s02.check_opening(plan))


def test_a_final_beat_id_that_matches_no_beat_is_caught():
    plan = _plan(final_beat_id="nope")
    assert any("final_beat_id" in p for p in s02.check_opening(plan))


def test_an_opening_beat_with_no_reversal_is_caught():
    """Openings need punchlines. This is the checkable form of that rule."""
    plan = _plan([_beat(refs=((1, 1), (1, 2), (2, 1)), reversal=None)])
    assert any("reversal" in p for p in s02.check_opening(plan))


def test_a_missing_bookend_statement_is_caught():
    """If the plan cannot say how the opening and the ending pair, they were chosen
    separately — and every school of screenwriting says that is backwards."""
    plan = _plan(bookend="   ")
    assert any("bookend" in p for p in s02.check_opening(plan))


def test_targets_yaml_defines_every_target_the_runner_can_ask_for():
    for name in ("feature", "episode10", "short60"):
        target = s02.load_target(name)
        assert target["pages"] > 0 and len(target["beats"]) == 2


def test_scene_index_truncates_summaries_to_keep_the_book_in_one_prompt():
    from agents import story_editor
    scenes = [{"chapter": 1, "scene": 1, "summary": "word " * 200, "dialogue": []}]
    row = story_editor.scene_index(scenes, summary_words=40)[0]
    assert len(row["summary"].split()) == 40
