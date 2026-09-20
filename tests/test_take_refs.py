"""Where the storyboard panel sits among a take's references.

OWNER 2026-09-20, asking what happened to the audio inputs -- which found a
risk I had not thought through. H3 ref2va drives LIPS from a voice wav, and it
needs a face to drive. Of ep05's 28 takes only four carry a voice (T06, T07,
T13, T27); the other 24 carry silence, because the narrator's 21 lines are
narration laid over the cut, not spoken on camera.

So the panel cannot simply replace the references everywhere. On a silent take
it can lead: nobody's mouth has to move. On a speaking take the character sheet
keeps its place at the front, because T07 is an over-the-shoulder and T27 a
medium, where the panel's face is small and half turned -- a worse driver than
a clean sheet.
"""
import pytest


def test_a_silent_take_leads_with_the_panel():
    from studio.take_refs import with_panel
    got = with_panel(["place.png", "narrator.png"], "panel.png", speaking=False)
    assert got[0] == "panel.png"
    assert got == ["panel.png", "place.png", "narrator.png"]


def test_a_speaking_take_keeps_the_sheet_in_front():
    from studio.take_refs import with_panel
    got = with_panel(["place.png", "narrator.png"], "panel.png", speaking=True)
    assert got[0] == "place.png"
    assert got[-1] == "panel.png", "the panel still informs it, from the back"


def test_no_panel_changes_nothing():
    from studio.take_refs import with_panel
    refs = ["place.png", "narrator.png"]
    assert with_panel(refs, None, speaking=False) == refs
    assert with_panel(refs, None, speaking=True) == refs


def test_a_panel_is_never_staged_twice():
    from studio.take_refs import with_panel
    got = with_panel(["panel.png", "place.png"], "panel.png", speaking=False)
    assert got.count("panel.png") == 1


def test_the_order_is_otherwise_untouched():
    """Everything the builder decided about the sheets stays decided."""
    from studio.take_refs import with_panel
    refs = ["a", "b", "c", "d"]
    assert with_panel(refs, "p", speaking=True)[:-1] == refs
    assert with_panel(refs, "p", speaking=False)[1:] == refs


def test_speaking_is_read_off_the_card_audio():
    from studio.take_refs import speaks
    assert speaks({"audio": "silence"}) is False
    assert speaks({"audio": [("voice_06.wav", 0.0)]}) is True
    assert speaks({}) is False
