"""A screenplay is not a transcript. Deterministic, agent-free.

The brick the screenwriter skill opens with: a screenplay may contain only four things
-- images, action, sound, dialogue. A scene built from ONE of them is not a scene. This
is the mechanical form of that rule, because nothing else in the pipeline was checking
it: the dossier hands the writer a dialogue list, and a model handed a list of lines
will happily return a list of lines.

No ratio is asserted here. I have no measured action:dialogue ratio from a real corpus,
and inventing one would be worse than checking the two things that need no corpus: a
scene with no action at all, and an unbroken volley nobody stages.
"""

from __future__ import annotations

from scripts.screenplay import step_04_render as s04
from studio.screenplay_spec import Scene, ScriptElement, Slug

SLUG = Slug(int_ext="INT", location_id="221b", location_name="221B Baker Street",
            time="DAY", text="INT. 221B BAKER STREET - DAY")


def _line(text="Quite.", who="holmes"):
    return ScriptElement(kind="dialogue", text=text, character=who)


def _act(text="He turns."):
    return ScriptElement(kind="action", text=text)


def _scene(elements, number=1):
    return Scene(number=number, beat_id="b1", slug=SLUG, elements=elements)


def test_a_balanced_scene_has_no_problems():
    scene = _scene([_act(), _line(), _line(who="watson"), _act("He pours the brandy."),
                    _line()])
    assert s04.balance_problems([scene]) == []


def test_a_scene_of_pure_dialogue_is_a_defect():
    """Nobody moves, nothing is seen. That is a radio play."""
    scene = _scene([_line(), _line(who="watson"), _line()])
    assert any("no action" in p for p in s04.balance_problems([scene]))


def test_an_action_only_scene_is_fine():
    """Silent scenes are legitimate screenwriting; silent SCREENPLAYS are not, and that
    is a whole-script question, not a per-scene one."""
    assert s04.balance_problems([_scene([_act(), _act("He looks back.")])]) == []


def test_an_unbroken_volley_is_flagged():
    scene = _scene([_act()] + [_line(who=f"c{i % 2}") for i in range(9)])
    assert any("consecutive" in p for p in s04.balance_problems([scene]))


def test_a_volley_broken_by_action_is_not_flagged():
    elements = [_act()]
    for i in range(9):
        elements.append(_line(who=f"c{i % 2}"))
        if i % 3 == 2:
            elements.append(_act("She sets down the cup."))
    assert s04.balance_problems([_scene(elements)]) == []


def test_the_volley_limit_is_configurable_and_inclusive():
    scene = _scene([_act()] + [_line() for _ in range(4)])
    assert s04.balance_problems([scene], max_volley=4) == []
    assert s04.balance_problems([scene], max_volley=3) != []


def test_problems_name_the_scene():
    scene = _scene([_line()], number=12)
    assert s04.balance_problems([scene])[0].startswith("scene 12:")


def test_an_empty_scene_is_reported_once_not_twice():
    """No elements at all is one problem, not 'no action' plus 'no dialogue'."""
    assert len(s04.balance_problems([_scene([])])) == 1


def test_transitions_do_not_count_as_action():
    """A CUT TO: stages nothing. Counting it would let a transition launder a scene
    that has no images in it."""
    scene = _scene([_line(), ScriptElement(kind="transition", text="CUT TO:")])
    assert any("no action" in p for p in s04.balance_problems([scene]))


def test_action_share_is_reported_as_a_measurement():
    scene = _scene([_act(), _line(), _line()])
    assert s04.action_share(scene) == 1 / 3


def test_action_share_of_an_empty_scene_is_zero_not_a_crash():
    assert s04.action_share(_scene([])) == 0.0
