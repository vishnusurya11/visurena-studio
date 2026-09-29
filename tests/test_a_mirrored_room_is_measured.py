"""panel_place (2026-09-28): a panel whose background is the staged room's
MIRROR is named -- ep14's Waterloo drew the rails on the right where the plate
has them on the left.  Advisory until calibrated; the ladder takes no rung."""
import numpy as np
from PIL import Image, ImageOps

from studio.measure import place


def room() -> Image.Image:
    """A room lit from the left: bright left wall, dark right wall, a window top-left."""
    a = np.tile(np.linspace(220, 40, 256), (256, 1)).astype(np.uint8)
    im = Image.fromarray(a).convert("RGB")
    im.paste((250, 250, 250), (20, 20, 90, 110))
    return im


def test_the_room_agrees_with_itself_and_disagrees_with_its_mirror():
    same = place.versus(room(), room())
    assert same["prof_same"] > 0.9 and not place.mirrored(same)
    flipped = place.versus(ImageOps.mirror(room()), room())
    assert flipped["prof_same"] < 0 and flipped["side_panel"] * flipped["side_ref"] < 0
    assert place.mirrored(flipped)


def test_a_flat_picture_says_nothing_about_a_side():
    flat = Image.new("RGB", (256, 256), (120, 120, 120))
    read = place.versus(flat, room())
    assert abs(read["side_panel"]) < place.SIDE_FLOOR and not place.mirrored(read)


def test_the_panel_judge_names_a_mirrored_panel_as_advice_only(tmp_path):
    """The verdict still passes; the ladder takes no rung for it."""
    import json
    from studio.judges import panel_eye
    from studio import grid_room, panel_ladder
    board = tmp_path / "storyboard"
    board.mkdir()
    room().resize((1024, 1024)).save(grid_room.room_path(tmp_path, "hall").parent.mkdir(parents=True) or grid_room.room_path(tmp_path, "hall"))
    ImageOps.mirror(room()).resize((1024, 1024)).save(board / "shot_00.png")
    room().resize((1024, 1024)).save(board / "shot_01.png")
    plan = {"setups": {"hall": {"described": "a hall"}},
            "shots": [{"index": 0, "setup": "hall", "size": "medium"}, {"index": 1, "setup": "hall", "size": "medium"}]}
    found = panel_eye.place_faults(tmp_path, plan, None)
    assert [f.where for f in found] == ["shot_00"] and found[0].severity == "advisory"
    assert "place" in panel_ladder.REDRAW_CANNOT_CURE
