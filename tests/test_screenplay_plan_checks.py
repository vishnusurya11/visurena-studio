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


def test_too_many_beats_is_still_caught():
    """The window is derived now, so the message changed - but overrunning it must
    still fail. TARGET allows 1-4 beats and the source has 3 scenes."""
    beats = [_beat(bid=f"b{i}", refs=((1, 1),)) for i in range(9)]
    plan = _plan(beats, omitted=[
        Omission(source=SceneRef(chapter=c, scene=s), reason="cut")
        for c, s in ((1, 2), (2, 1))])
    assert any("outside window" in p for p in s02.check(plan, DOSSIER, TARGET))


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


# --- the beat window must fit the SOURCE, not just the target (2026-08-28) ---------
#
# Metamorphosis failed with "8 beats outside target window 18-26". It is a 22,000-word
# novella with 21 source scenes, and 8 beats is right for it. Demanding 18 sequences of
# a book that has 21 scenes would mean sequences of one scene each, which is not what a
# sequence is.
#
# Coppola's notebook is the ratio: 50 sections over 225 slug lines, about 4.5 scenes to
# a sequence. So the expected beat count follows from the SOURCE, and the target's window
# is a cap on ambition rather than a floor a short book must meet.

def test_a_novella_is_not_asked_for_feature_length_beat_counts():
    from scripts.screenplay.step_02_plan import beat_window
    low, high = beat_window({"beats": [18, 26]}, source_scenes=21)
    assert low <= 8 <= high


def test_a_full_length_novel_keeps_the_targets_window():
    from scripts.screenplay.step_02_plan import beat_window
    assert beat_window({"beats": [18, 26]}, source_scenes=92) == (18, 26)


def test_the_window_never_exceeds_the_target():
    """The target is a budget. A long book does not get to overrun it."""
    from scripts.screenplay.step_02_plan import beat_window
    _, high = beat_window({"beats": [18, 26]}, source_scenes=400)
    assert high == 26


def test_the_window_is_never_below_one():
    from scripts.screenplay.step_02_plan import beat_window
    low, high = beat_window({"beats": [18, 26]}, source_scenes=2)
    assert low >= 1 and high >= low


def test_a_book_with_no_scenes_still_yields_a_usable_window():
    from scripts.screenplay.step_02_plan import beat_window
    low, high = beat_window({"beats": [18, 26]}, source_scenes=0)
    assert low >= 1 and high >= low


def test_the_check_uses_the_derived_window():
    from scripts.screenplay.step_02_plan import check
    from studio.screenplay_spec import Beat, Omission, SceneRef, ScreenplayPlan
    dossier = {"scenes": [{"chapter": 1, "scene": n} for n in range(1, 22)],
               "characters": [{"id": "gregor"}], "locations": []}
    beats = [Beat(id=f"b{i}", intent="i", unifying_aspect="u", protagonist="gregor",
                  objective="to o", boundary_event="e", transfer="transfer",
                  reversal="r", source=[SceneRef(chapter=1, scene=i)])
             for i in range(1, 9)]
    plan = ScreenplayPlan(spine="s", logline="l", opening_beat_id="b1",
                          final_beat_id="b8", bookend="paired", beats=beats,
                          omitted=[Omission(source=SceneRef(chapter=1, scene=n),
                                            reason="cut") for n in range(9, 22)])
    assert not [p for p in check(plan, dossier, {"pages": 100, "beats": [18, 26]})
                if "beats outside" in p]


def test_a_protagonist_given_by_name_resolves_to_its_id():
    """The editor returns "Alice" and "Buck" - names, because that is what a person
    calls a protagonist. Demanding a canonical id failed two books outright when the
    registry plainly contained them."""
    from scripts.screenplay.step_02_plan import resolve_protagonist
    registry = [{"id": "alice", "name": "Alice", "aliases": []},
                {"id": "buck", "name": "Buck", "aliases": ["the dog"]}]
    assert resolve_protagonist("Alice", registry) == "alice"
    assert resolve_protagonist("the dog", registry) == "buck"


def test_an_id_the_editor_got_right_passes_through():
    from scripts.screenplay.step_02_plan import resolve_protagonist
    assert resolve_protagonist("alice", [{"id": "alice", "name": "Alice"}]) == "alice"


def test_a_genuinely_unknown_protagonist_still_fails():
    from scripts.screenplay.step_02_plan import resolve_protagonist
    assert resolve_protagonist("Moriarty", [{"id": "alice", "name": "Alice"}]) is None


def test_the_upper_bound_allows_more_beats_than_the_ratio_suggests():
    """18 beats over 37 source scenes is two scenes to a sequence - tight, but a real
    choice for a short work. The ratio sets an EXPECTATION, not a ceiling; the ceiling
    is the source itself."""
    from scripts.screenplay.step_02_plan import beat_window
    low, high = beat_window({"beats": [18, 26]}, source_scenes=37)
    assert low <= 18 <= high


def test_there_are_never_more_beats_than_source_scenes():
    from scripts.screenplay.step_02_plan import beat_window
    _, high = beat_window({"beats": [18, 26]}, source_scenes=5)
    assert high <= 5


# --- unaccounted scenes (2026-08-28) -----------------------------------------------
#
# Black Beauty died on "scene (26, 8) is in no beat and not in `omitted`". The rule is
# right - silent dropping is THE failure mode of adaptation - but the editor missing one
# scene of two hundred should not cost the book.
#
# Code can satisfy the invariant the check exists to protect: sweep the unaccounted
# scenes into `omitted` with a machine-written reason that says plainly nobody chose it.
# The scene stays visible, which is the whole point, and the book survives.
#
# Above a threshold it still fails, because an editor that ignored half the book has not
# planned anything and sweeping that up would hide a real failure.

def _plan_missing(n_missing, n_total=20):
    from studio.screenplay_spec import Beat, SceneRef, ScreenplayPlan
    covered = n_total - n_missing
    beats = [Beat(id="b1", intent="i", unifying_aspect="u", protagonist="watson",
                  objective="to o", boundary_event="e", transfer="transfer",
                  reversal="r",
                  source=[SceneRef(chapter=1, scene=i) for i in range(1, covered + 1)])]
    return ScreenplayPlan(spine="s", logline="l", opening_beat_id="b1",
                          final_beat_id="b1", bookend="paired", beats=beats)


def _dossier(n_total=20):
    return {"scenes": [{"chapter": 1, "scene": i} for i in range(1, n_total + 1)],
            "characters": [{"id": "watson", "name": "Dr Watson"}], "locations": []}


def test_a_few_unaccounted_scenes_are_swept_into_omitted():
    from scripts.screenplay.step_02_plan import account_for_every_scene
    plan = _plan_missing(2)
    swept = account_for_every_scene(plan, _dossier())
    assert swept == 2
    assert len(plan.omitted) == 2


def test_the_swept_reason_says_nobody_chose_it():
    from scripts.screenplay.step_02_plan import account_for_every_scene
    plan = _plan_missing(1)
    account_for_every_scene(plan, _dossier())
    assert "not accounted for" in plan.omitted[0].reason.lower()


def test_a_plan_that_accounts_for_everything_is_untouched():
    from scripts.screenplay.step_02_plan import account_for_every_scene
    plan = _plan_missing(0)
    assert account_for_every_scene(plan, _dossier()) == 0


def test_an_editor_that_ignored_most_of_the_book_still_fails():
    """Sweeping that up would hide a real planning failure."""
    from scripts.screenplay.step_02_plan import account_for_every_scene
    import pytest
    with pytest.raises(ValueError, match="did not account"):
        account_for_every_scene(_plan_missing(15), _dossier())


def test_after_sweeping_the_check_passes():
    from scripts.screenplay.step_02_plan import account_for_every_scene, check
    plan, dossier = _plan_missing(2), _dossier()
    account_for_every_scene(plan, dossier)
    assert not [p for p in check(plan, dossier, {"pages": 100, "beats": [1, 4]})
                if "silent drop" in p]
