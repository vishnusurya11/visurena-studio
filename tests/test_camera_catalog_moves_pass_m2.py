"""The camera catalog's moves are camera moves (owner 2026-09-19).

`docs/calibration/camera_catalog.md` is the vocabulary from WotW ep02 on, and
M2 ("the head names no camera move") knew only push/pull/track/pan/tilt/crane/
orbit, so a locked-off frame, a crane that descends or rises, and a rack of
focus were refused as no move at all -- which would have pushed every plan back
to the pans that made ep01 an orbit reel."""
import pytest

from studio.episode_spec import motion_faults
from studio import episode_ref_official as ro

HEADS = [
    "The camera holds a locked-off frame",
    "The camera descends from the lemon sky over the far pines to the heather",
    "The camera rises above the bright seam, looking down over the crusted lid",
    "The camera racks focus from the white palings to Henderson behind them",
]


@pytest.mark.parametrize("head", HEADS)
def test_a_catalog_move_is_a_camera_move(head):
    codes = [c for c, _ in motion_faults(f"{head}; he lifts his arm; he turns his head.")]
    assert "M2" not in codes


@pytest.mark.parametrize("head", HEADS)
def test_the_take_sentence_keeps_the_catalog_move(head):
    said = ro.camera_sentence(f"{head}; he lifts his arm; he turns his head.", 0, 4)
    assert said.startswith("The camera ") and head.split(" ", 3)[3].split(",")[0] in said
