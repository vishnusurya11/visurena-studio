"""A grid with no WIDE cell is never handed its setup's establishing-wide geometry.

G-SCALE (2026-09-22) refuses a non-wide shot carrying its setup's wide geometry, and
7ddba20 (09-23) briefed a tight grid's place; 97b621d (09-28) then appended the
geometry and the landmark to EVERY grid.  Jekyll ep04 (2026-10-27): 15 of 27 panels
came back two sizes wider than asked (ep01 5, ep02 8, ep03 8); shot 1, "the face fills
the picture", came back a medium holding the trunk, the window, the washstand and the
bed -- every item the appended "In the establishing wide ..." listed.
"""
from studio.storyboard_grid import grid_prompt_v2

PLACE = ([2], "A narrow attic bedroom under a sloping plaster ceiling")
GEO = "In the establishing wide the box trunk sits at the BOTTOM LEFT."


def cell(size: str) -> dict:
    return {"size": size, "body": "the woman at the window", "cut": "the picture cuts at the shoulders",
            "who": [], "extras": 0}


def test_a_close_picture_gets_no_wide_geometry():
    assert GEO not in grid_prompt_v2([cell("BIG CLOSE-UP")], 1, 1, PLACE, [], 3, geometry=GEO)


def test_a_medium_and_an_extreme_close_get_none_either():
    assert GEO not in grid_prompt_v2([cell("MEDIUM")], 1, 1, PLACE, [], 3, geometry=GEO)
    assert GEO not in grid_prompt_v2([cell("EXTREME CLOSE-UP")], 1, 1, PLACE, [], 3, geometry=GEO)


def test_a_grid_holding_a_wide_keeps_it():
    text = grid_prompt_v2([cell("WIDE"), cell("BIG CLOSE-UP")], 2, 1, PLACE, [], 3, geometry=GEO)
    assert GEO in text
