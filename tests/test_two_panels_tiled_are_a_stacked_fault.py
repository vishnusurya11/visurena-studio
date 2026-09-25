"""Two panels tiled into one frame with a pale gutter read as stacked.

The synthetic generator draws the fault the owner saw on a published master
(two pictures in one frame, split by a white line), and the shipped
`panel_dq.stacked` measure sees it over its wall while a single panel of the
same texture reads under.  The generator's row is `synthetic`, class
`stacked_pictures`, and counts only in its own column.
"""
import numpy as np
from PIL import Image

from studio import panel_dq, synth_faults


def panel(seed, size=(253, 512)):
    rng = np.random.default_rng(seed)
    return Image.fromarray(rng.integers(20, 110, (size[1], size[0], 3), dtype=np.uint8))


def test_the_tiled_pair_reads_stacked_and_one_panel_does_not():
    tiled = synth_faults.tile_two(panel(1), panel(2), gutter=6)
    assert tiled.size == (512, 512)
    assert panel_dq.stacked(np.asarray(tiled)) > panel_dq.STACKED
    assert panel_dq.stacked(np.asarray(panel(1, (512, 512)))) < panel_dq.STACKED


def test_a_drawn_gutter_alone_reads_stacked():
    lined = synth_faults.draw_gutter(panel(3, (512, 512)), axis="y", width=6)
    assert panel_dq.stacked(np.asarray(lined)) > panel_dq.STACKED


def test_the_row_is_synthetic_stacked():
    row = synth_faults.row("00000000000000", "ep01", "panel", "casebook/synth/shot_00_stacked.png", "stacked_pictures")
    assert row.verdict_by == "synthetic" and row.fault_class == "stacked_pictures"


def test_a_duplicated_crop_and_a_resaved_reference_change_the_picture():
    src = panel(4, (128, 128))
    doubled = synth_faults.duplicate_crop(src, (0, 0, 40, 40), to=(80, 80))
    assert (np.asarray(doubled)[80:120, 80:120] == np.asarray(src)[0:40, 0:40]).all()
    resaved = synth_faults.resave_reference(src, quality=30)
    assert resaved.size == src.size and (np.asarray(resaved) != np.asarray(src)).any()
