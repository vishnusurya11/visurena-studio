"""A `loc-` reference lives with the book's locations, not in the episode's cells.

MEASURED 2026-09-17: episode 14's first render with the book's own location
pictures died at the first take -- `cannot stage missing image:
episodes/ep14/boards/cells/loc-221b_baker_street.png`. Every prefix but this one
was routed; an unrouted name falls through to the cells folder, which is exactly
the fault this function exists to prevent.
"""
from pathlib import Path

from studio.episode_seq_board import picture_path

BOOK, BOARDS = Path("book"), Path("boards")


def test_a_location_goes_to_the_book_s_locations():
    assert picture_path(BOARDS, BOOK, "loc-221b_baker_street.png") == \
        BOOK / "refs" / "locations" / "loc-221b_baker_street.png"


def test_the_other_prefixes_are_unchanged():
    assert picture_path(BOARDS, BOOK, "char-john_watson_indoor.png") == \
        BOOK / "refs" / "characters" / "char-john_watson_indoor.png"
    assert picture_path(BOARDS, BOOK, "plate_cell_dawn.png") == BOARDS / "plates" / "plate_cell_dawn.png"
    assert picture_path(BOARDS, BOOK, "Q11_0.png") == BOARDS / "cells" / "Q11_0.png"
