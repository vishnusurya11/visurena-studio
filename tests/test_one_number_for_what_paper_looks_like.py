"""The sheet detector and the take guard must not own separate ideas of paper.

Two places in this pipeline decide whether a bright flat run is sheet paper:

    `episode_board.bands`     finds the gutters ON THE SHEET, to cut cells between
    `episode_gutter.band`     finds leaked paper IN A CELL OR TAKE, to crop it off

They had the same two numbers written out twice, 190.0 and 30.0, and when the
take guard's floor was recalibrated for Part Two's desert the sheet detector kept
the London one. `white_lines` had already learned this lesson the other way round
-- its docstring ends "so it owns the number and this asks for it" -- and it was
still true of the sheet.

MEASURED on episode 9's `seq_valley_rim_0_strict.png`, a 2x2 of the valley of
Utah at sunrise. A 2x2 needs exactly one row band and one column band, and the
detector found THREE row bands:

    rows   16-17     depth   1   mean 190.1   std 13.87   <- sky
    rows   18-118    depth 100   mean 196.6   std 16.40   <- sky, 100 rows deep
    rows 1015-1026   depth  11   mean 247.7   std  2.12   <- the real gutter
    cols 1018-1030   depth  12   mean 251.7   std  2.49   <- the real gutter

So `cell_boxes` fell back to cutting the sheet in flat halves, `gutters_ok` went
False, and `qc` failed an episode whose 28 takes all scored 100/100 and whose
master passed edit integrity frame for frame.

Real gutters read std 2.1-2.5 at mean 248-252. The skies read 13.9-16.4 at mean
190-197. That is the same population split the take guard was recalibrated on,
which is the point: one fact about paper, one number.
"""
import numpy as np

from studio import episode_board as board
from studio import episode_gutter as gutter


def test_the_sheet_detector_asks_the_guard_what_paper_looks_like():
    assert board.GUTTER_WHITE is gutter.WHITE
    assert board.GUTTER_FLAT is gutter.FLAT


def sheet(side: int = 2048) -> np.ndarray:
    """A 2x2 whose top half is pale sky and whose gutters are real paper."""
    rng = np.random.default_rng(5)
    g = np.full((side, side), 70.0) + rng.normal(0, 25.0, (side, side))
    g[18:118] = 196.6 + rng.normal(0, 16.4, (100, side))      # sky across both panels
    g[1015:1026] = 247.7 + rng.normal(0, 2.1, (11, side))     # the row gutter
    g[:, 1018:1030] = 251.7 + rng.normal(0, 2.5, (side, 12))  # the column gutter
    return g


def test_a_hundred_rows_of_sky_is_not_a_gutter():
    rows = board.bands(sheet(), 0)
    assert len(rows) == 1, f"expected the one real gutter, found {rows}"
    assert 1000 < rows[0][0] < 1030


def test_the_real_gutters_are_still_found_on_both_axes():
    g = sheet()
    assert len(board.bands(g, 0)) == 1 and len(board.bands(g, 1)) == 1


def test_the_cells_are_cut_between_the_found_gutters_not_on_flat_halves():
    boxes = board.cell_boxes(sheet(), cols=2, rows=2)
    assert len(boxes) == 4
    # the top-left cell stops AT the gutter, so its bottom edge is the band's start
    assert boxes[0][3] == 1015 and boxes[0][2] == 1018
