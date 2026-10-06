"""The cure table routes the two clone-text gates: a G-GHOST row to the $0
clause surgeon, a G-TWICE row to the one-shot llm rewrite, and a creative
row still to nobody (the writer's, one field at a time)."""
from __future__ import annotations

from studio import plan_cures as pc

GHOST_ROW = ("    G-GHOST shot 11: frame stages brother's shoulder and brother is not in "
             "faces ['captain'], measured brother against a face, or absent")
TWICE_ROW = ("    G-TWICE shot 20: frame+at_rest places curate at both 'scullery' and "
             "'kitchen'; one person holds one position per picture, measured 2 against 1")


def test_a_ghost_row_routes_to_the_clause_surgeon():
    assert pc.cure_for(GHOST_ROW) == "ghost_limbs"


def test_a_twice_row_routes_to_the_position_rewrite():
    assert pc.cure_for(TWICE_ROW) == "one_position"


def test_a_creative_row_still_maps_to_nobody():
    row = "G-STORY shot 3: first dialogue line at 90.0 s of 150.0 s projected, measured 0.6 against 0.25"
    assert pc.cure_for(row) is None
