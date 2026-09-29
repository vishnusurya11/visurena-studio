"""One room per setup (2026-09-28, docs/audit/2026-09-28_grid_place_constancy_plan.md):
the grid holding a setup's widest shot is its anchor, drawn first; its widest
cell is cut to storyboard/anchors/<setup>.png; every sibling grid stages that
room.  ep14 drew two biology classrooms, a mirrored Waterloo and an attic that
became a street because each of a setup's 2-6 renders re-dressed the room."""
from pathlib import Path

from PIL import Image

from studio import grid_room as gr

SHOTS = [{"index": 0, "setup": "attic", "size": "medium"}, {"index": 1, "setup": "attic", "size": "close"},
         {"index": 2, "setup": "attic", "size": "wide"}, {"index": 3, "setup": "attic", "size": "insert"},
         {"index": 4, "setup": "street", "size": "full"}, {"index": 5, "setup": "street", "size": "wide"}]
ROWS = [{"setup": "attic", "cols": 2, "rows": 1, "tag": "a", "shots": [0, 3]},
        {"setup": "attic", "cols": 1, "rows": 1, "tag": "b", "shots": [2]},
        {"setup": "attic", "cols": 1, "rows": 1, "tag": "s01", "shots": [1]},
        {"setup": "street", "cols": 2, "rows": 1, "shots": [4, 5]}]


def test_the_anchor_is_the_widest_shot_then_the_earliest():
    assert gr.anchor_shot(SHOTS, "attic") == 2
    assert gr.anchor_shot(SHOTS, "street") == 5
    assert gr.anchor_shot(SHOTS, "nowhere") is None


def test_the_anchor_grid_is_drawn_before_its_siblings_and_setups_keep_their_order():
    order = gr.draw_order(ROWS, SHOTS)
    assert [r["shots"] for r in order] == [[2], [0, 3], [1], [4, 5]]


def test_only_a_sibling_stages_the_room_and_only_once_it_exists(tmp_path):
    assert gr.room_for(tmp_path, "attic", [2], 2) is None            # the anchor grid stages the plate
    assert gr.room_for(tmp_path, "attic", [0, 3], 2) is None         # not cut yet
    room = gr.room_path(tmp_path, "attic")
    room.parent.mkdir(parents=True)
    room.write_bytes(b"room")
    assert gr.room_for(tmp_path, "attic", [0, 3], 2) == room


def test_the_plate_joins_the_room_only_for_a_wide_or_full():
    assert not gr.stages_plate([SHOTS[0], SHOTS[3]])
    assert gr.stages_plate([SHOTS[4]])


def test_siblings_are_the_other_grids_of_an_anchor_row():
    assert [r["shots"] for r in gr.siblings(ROWS, ROWS[1], SHOTS)] == [[0, 3], [1]]
    assert gr.siblings(ROWS, ROWS[0], SHOTS) == []                  # not the anchor
    assert gr.siblings(ROWS, ROWS[3], SHOTS) == []                  # a setup of one grid


def test_the_room_is_the_anchor_cell_square_at_panel_size(tmp_path):
    grid = tmp_path / "g.png"
    canvas = Image.new("RGB", (2048, 1024), "white")
    canvas.paste(Image.new("RGB", (1000, 1000), (200, 30, 30)), (12, 12))      # slot 0: red
    canvas.paste(Image.new("RGB", (1000, 1000), (30, 30, 200)), (1036, 12))    # slot 1: blue
    canvas.save(grid)
    row = {"setup": "attic", "cols": 2, "rows": 1, "shots": [0, 2]}
    out = gr.cut_room(grid, row, 2, gr.room_path(tmp_path, "attic"))
    im = Image.open(out)
    assert im.size == (1024, 1024) and im.getpixel((512, 512))[2] > 150
    assert gr.room_stale(tmp_path, "attic", grid) is False
    assert gr.room_stale(tmp_path, "other", grid) is True
