"""A place's name ends at its first sentence, not only at its first comma.

Jekyll ep04 (2026-10-27): the writer described each setup as short sentences with
no early comma, so `short_place` (the take summary, the soundscape) and
`place_head` (a tight grid's brief place) handed on the whole inventory -- 44,
35 and 99 words where ep01-ep03 ran 2-30.  T10 and T12 (police_cell, 99 words)
opened ~8 frames on the empty cell H3 drew from those words, then hard-cut to
the close; the tight panels drew the trunk, the washstand and the bed around a
face the shot asked to fill the frame.
"""
from studio.episode_ref_official import short_place
from studio.storyboard_grid import brief_place, place_head

CELL = ("A bare whitewashed police station cell with a low vaulted brick ceiling. Grey morning daylight "
        "falls in from a small barred window high in the left wall and lays a pale barred patch across a "
        "heavy wooden table at the centre. A long trestle bier under a white sheet stands against the back wall.")


def test_the_take_names_the_place_by_its_first_sentence():
    assert short_place(CELL) == "a bare whitewashed police station cell with a low vaulted brick ceiling"


def test_a_tight_grid_names_the_place_by_its_first_sentence():
    assert place_head(CELL) == "A bare whitewashed police station cell with a low vaulted brick ceiling"
    assert brief_place(CELL, "grey morning daylight") == (
        "A bare whitewashed police station cell with a low vaulted brick ceiling; the light is grey morning daylight")


def test_a_title_stop_does_not_end_the_name():
    assert short_place("Dr. Lanyon's dining room in Cavendish Square. A fire burns.") == \
        "Dr. Lanyon's dining room in Cavendish Square"
    assert place_head("Mr. Hyde's rooms in Soho. Wine on the table.") == "Mr. Hyde's rooms in Soho"
