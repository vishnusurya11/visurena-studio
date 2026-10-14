"""An automatic camera rewrite is linted before it can reach a render.

Jekyll ep01 (2026-10-13, MOTION.md cause 6), the ran prompts after the cures:
    "pushes in toward the face of the man about"     (T05, T19, T23: "man about town" cut at 6 words)
    "pans from the third to the coat"                (T12: a layout word taken as an aim)
    "tracks beside the lawyer's shoulder across the whole"  (T26: the old head's tail kept as aim)
    "at a good walk at a normal walking pace"        (T11: a pace said twice)
and "a few yards", "a few paces", "a man's height" survived the amount strip on
seven takes -- H3 obeys direction, not amount.
"""
from __future__ import annotations

from studio import camera_lint as cl


def test_a_name_cut_mid_phrase_is_a_fault_and_is_repaired():
    head = "The camera pushes in toward the face of the man about"
    assert cl.faults(head)
    assert cl.repair_aim("the face of the man about") == "the face of the man"


def test_a_layout_word_is_never_an_aim():
    assert any("layout" in f for f in cl.faults("The camera pans from the third to the coat"))


def test_the_old_heads_tail_is_not_an_aim():
    assert cl.faults("The camera tracks beside the lawyer's shoulder across the whole")
    assert cl.repair_aim("the lawyer's shoulder across the whole") == "the lawyer's shoulder"


def test_a_clean_head_passes():
    assert cl.faults("The camera pushes in toward the face of the lawyer, across the whole shot") == []
    assert cl.faults("The camera holds a locked-off frame") == []


def test_every_distance_is_stripped():
    for said in ("The camera tracks sideways to the right a few yards past the green door",
                 "The camera tracks beside the lawyer a few paces along the kerb",
                 "The camera rises a man's height above the corner",
                 "The camera tracks sideways to the right, travelling two strides, past the door"):
        out = cl.strip_amounts(said)
        assert not cl.AMOUNTS.search(out), out
        assert out.startswith("The camera")
    assert cl.strip_amounts("The camera rises a man's height above the corner") == \
        "The camera rises above the corner"


def test_a_pace_said_twice_keeps_the_first():
    said = "the little man stumps along from the LEFT at a good walk at a normal walking pace, his face calm"
    assert cl.one_pace(said) == "the little man stumps along from the LEFT at a good walk, his face calm"
    assert any("pace" in f for f in cl.faults(said))


def test_the_take_prompt_never_adds_a_second_pace():
    from studio import episode_ref_official as ro
    said = "the little man stumps along the pavement at a good walk, his face calm"
    assert ro.paced(said) == said


def test_the_take_prompt_strips_every_distance():
    from studio import episode_ref_official as ro
    assert "yards" not in ro.without_amount("The camera tracks sideways to the right a few yards past the door")


def test_the_rebalance_cure_never_aims_at_a_layout_word():
    from studio import move_rebalance as mr
    assert {"third", "thirds", "quarter", "half"} <= mr.NOT_AIMS


def test_the_rebalance_cure_refuses_a_garbled_head():
    from types import SimpleNamespace
    from studio import move_rebalance as mr
    shot = SimpleNamespace(index=3, size="medium", motion="the man waits", camera="", at_rest="the man",
                           frame="", faces=[], extras=0, setup="", still=False)
    bad = mr.head_faults(shot, "The camera pushes in toward the face of the man about", "", "", SimpleNamespace(crowd=""))
    assert any("CAMERA-LINT" in f for f in bad)


def test_the_ladder_aim_is_repaired():
    from studio import take_ladder
    assert take_ladder.aim_of("The camera pushes in toward the face of the man about town; he speaks") \
        in ("the face of the man about town", "the face of the man")
    assert not cl.faults(f"The camera tracks beside {take_ladder.aim_of('The camera tracks beside the lawyer shoulder across the whole shot; he talks')}")


def test_a_distance_goes_with_its_for():
    """WotW ep18 T05: "tracks behind the pair toward the church tower for twenty feet across the whole shot"."""
    assert cl.strip_amounts("The camera tracks behind the pair toward the tower for twenty feet across the whole shot") \
        == "The camera tracks behind the pair toward the tower across the whole shot"


def test_the_pace_lint_accepts_the_plans_own_pace():
    from studio import episode_ref_official as ro
    assert ro.named_pace("he stumps along at a good walk") and ro.named_pace("he walks at a normal walking pace")
    assert not ro.named_pace("he walks along the pavement")
