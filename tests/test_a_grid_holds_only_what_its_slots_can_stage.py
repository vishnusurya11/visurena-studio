"""ep17 (owner 2026-10-04: "shot 14 is shit .. we had character sheets before ..
so use them").  The image model stages three pictures a grid, the place takes
one, so a grid can show two sheets.  Steamer grid a held the captain (shot 13),
the brother (shot 15) and the wading fighting-machine (shot 14): two people
filled the slots, the machine's sheet was dropped without a word, and the
drawer invented a naked humanoid from the bare word 'Martian'.  A grid holds
only the people and props its slots can stage: a shot whose needs would push
the grid past the budget opens a new grid.  $0: pure data."""
from __future__ import annotations

from studio import grid_layout


def shots(*sizes):
    return [{"index": i, "setup": "deck", "size": s} for i, s in enumerate(sizes)]


def test_a_shot_that_would_overfill_the_slots_opens_a_new_grid():
    needs = {0: {"captain", "ram"}, 1: {"machine"}, 2: {"brother", "ram"},
             3: {"machine", "ram"}, 4: {"machine", "ram"}, 5: {"captain"}}
    rows = grid_layout.layout({"deck": {}}, shots(*["medium"] * 6), needs=needs)
    assert [r["shots"] for r in rows] == [[0], [1], [2], [3, 4], [5]]


def test_every_grid_needs_at_most_the_budget():
    needs = {0: {"a"}, 1: {"b"}, 2: {"c"}, 3: {"a"}}
    for r in grid_layout.layout({"deck": {}}, shots(*["medium"] * 4), needs=needs):
        assert len(set().union(*(needs[i] for i in r["shots"]))) <= grid_layout.BUDGET


def test_shots_that_share_their_sheets_still_share_a_grid():
    needs = {0: {"brother"}, 1: {"brother", "ram"}, 2: {"ram"}, 3: set()}
    rows = grid_layout.layout({"deck": {}}, shots(*["medium"] * 4), needs=needs)
    assert [r["shots"] for r in rows] == [[0, 1, 2, 3]]


def test_without_needs_the_layout_is_unchanged():
    plain = grid_layout.layout({"deck": {}}, shots(*["medium"] * 5))
    assert [r["shots"] for r in plain] == [[0, 1, 2], [3, 4]]
