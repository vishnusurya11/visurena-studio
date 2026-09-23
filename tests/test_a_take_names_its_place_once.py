"""A take whose storyboard panel is staged names its place once, briefly.

Prompt-builder audit, 2026-09-23, over 99 rendered prompts: the place was
stated three times in 98 of them -- the summary, "The shot is inside this
place:" and the soundscape -- and ep09 T15, a 3-second rubble insert, opened
0.5 s on the burning lawn its prompt named three times, then hard-cut to the
rubble. The staged panel IS the room. The soundscape's "low murmur of the
people at work nearby" sat in 49 prompts (8 of them inserts) while 0 of 99
carried a life sentence, so it invited extras nothing else asked for.
"""
from studio import episode_ref_official as ro

LAWN = ("the same walled lawn on the crest of Maybury Hill with the valley below it on fire: the broken "
        "roof line of the Oriental College and a half-fallen church tower burning above the garden wall")


def test_the_short_place_stops_at_a_colon():
    assert ro.short_place(LAWN) == "the same walled lawn on the crest of Maybury Hill with the valley below it on fire"


def test_a_staged_panel_means_the_block_does_not_restate_the_place():
    assert not ro.says_place({"cells_staged": False, "panel": True})
    assert ro.says_place({"cells_staged": False, "panel": False})
    assert not ro.says_place({"cells_staged": True})


def test_a_staged_panel_lowers_the_floor_and_keeps_the_ceiling():
    """The panel carries the room, so the floor falls to the picture band's 150;
    the 360 ceiling is against padding, and ep09 T22 (a dialogue close) has 243
    words of core alone."""
    assert ro.band_for({"cells_staged": False, "panel": True}) == (ro.LOW_BLOCK, ro.HIGH_BLOCK_REFS)
    assert ro.band_for({"cells_staged": False}) == ro.block_band(False)


def test_the_soundscape_is_short_and_names_no_place():
    said = ro.soundscape(LAWN, outdoors=True)
    assert len(said.split()) <= 15 and "Maybury" not in said and "lawn" not in said


def test_people_are_heard_only_when_a_block_puts_them_there():
    assert "murmur" not in ro.soundscape(LAWN, crowd="sappers at work", outdoors=True, life=False)
    assert "people" in ro.soundscape(LAWN, crowd="sappers at work", outdoors=True, life=True)


def test_the_indoor_soundscape_carries_no_stillness_word():
    """'Still indoor air' tripped L2 STILLNESS on ep09 T19/T20 in the first cut."""
    assert "still" not in ro.soundscape("the bar of the Spotted Dog", outdoors=False).lower()
