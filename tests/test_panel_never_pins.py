"""A storyboard panel informs a take; it must never pin it.

MEASURED, ALREADY, IN THIS REPO -- and found before spending a GPU hour on it.
`episode_ref_official` carries the note: staging a composed still and calling it
"fully_preserved - subject placement, wardrobe and light" froze ep03 T02, which
came back at similarity 1.000 to its cell with 0.12 frame-to-frame change: the
still reproduced, not animated. It is the same fault as a last-frame pin
(`NO_ENDS`), and the same shape as the composed frame zero the owner rejected
outright in August.

So the panel may be staged only with a relation that hands the FRAMING back to
the words. It carries the place, the people and their clothes; the camera move
and the action come from the prompt, as they always did.
"""
import pytest


def test_the_panel_is_never_fully_preserved():
    from studio.take_refs import panel_retention
    said = panel_retention(4)
    assert "fully_preserved" not in said
    assert "weak_reference" in said, (
        "this pipeline's own word for a picture that informs without pinning")


def test_the_retention_line_carries_no_negation():
    """MiniMax cannot read one, and the prompt builder refuses the take over it:
    "a fence built out of the word you are avoiding is a summons"."""
    from studio.take_refs import panel_retention
    from studio.episode_ref_official import negations
    assert not negations(panel_retention(4))


def test_the_panel_hands_the_framing_back_to_the_words():
    from studio.take_refs import panel_retention
    said = panel_retention(4).lower()
    assert "framing" in said and "camera" in said
    assert "come from the camera sentence" in said


def test_the_panel_keeps_who_and_where():
    from studio.take_refs import panel_retention
    said = panel_retention(4).lower()
    assert "clothes" in said or "wardrobe" in said
    assert "place" in said or "location" in said


def test_it_cites_its_own_slot():
    from studio.take_refs import panel_retention, panel_definition
    assert "<Picture 4>" in panel_retention(4)
    assert "<Picture 4>" in panel_definition(4)


def test_the_definition_says_it_is_a_storyboard_frame():
    from studio.take_refs import panel_definition
    assert "storyboard" in panel_definition(2).lower()


def test_neither_line_ever_says_first_frame():
    """"first frame" is the clause that pinned ep03 T02."""
    from studio.take_refs import panel_definition, panel_retention
    for said in (panel_definition(3), panel_retention(3)):
        assert "first frame" not in said.lower()
