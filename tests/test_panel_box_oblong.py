"""A grid is not always square, and a square-only crop cuts the wrong panels.

MEASURED 2026-09-22 on ep09: every grid before it was N x N, so `panel_box`
took ONE `size` and divided it by cols for the width and by rows for the
height. Episode 9's setups hold 2, 3, 5 and 8 shots, which do not make
squares: its grids are 2x1, 3x1 and 4x2, and on a 2048x1024 grid the old
arithmetic asks for a cell 1024 wide and 2048 tall -- half of it off the
bottom of the picture.

The trim stays what it was. A white seam down one edge of a reference is a
picture element as far as H3 is concerned, not a gutter.
"""
import pytest

from studio.storyboard_grid import panel_box


def test_a_square_grid_crops_exactly_as_it_always_did():
    assert panel_box(0, cols=2, rows=2, size=2048, trim=16) == (16, 16, 1008, 1008)
    assert panel_box(3, cols=2, rows=2, size=2048, trim=16) == (1040, 1040, 2032, 2032)


def test_a_size_may_be_given_as_width_and_height():
    assert panel_box(0, cols=2, rows=2, size=(2048, 2048), trim=16) == (16, 16, 1008, 1008)


def test_a_two_by_one_grid_crops_two_side_by_side_cells():
    assert panel_box(0, cols=2, rows=1, size=(2048, 1024), trim=0) == (0, 0, 1024, 1024)
    assert panel_box(1, cols=2, rows=1, size=(2048, 1024), trim=0) == (1024, 0, 2048, 1024)


def test_a_three_by_one_grid_crops_three_in_a_row():
    assert panel_box(2, cols=3, rows=1, size=(3072, 1024), trim=0) == (2048, 0, 3072, 1024)


def test_a_four_by_two_grid_wraps_onto_the_second_row():
    assert panel_box(4, cols=4, rows=2, size=(4096, 2048), trim=0) == (0, 1024, 1024, 2048)
    assert panel_box(7, cols=4, rows=2, size=(4096, 2048), trim=0) == (3072, 1024, 4096, 2048)


def test_a_one_by_one_grid_is_the_whole_picture_less_its_trim():
    assert panel_box(0, cols=1, rows=1, size=(1024, 1024), trim=16) == (16, 16, 1008, 1008)


def test_no_crop_ever_runs_off_the_picture():
    for n in range(6):
        box = panel_box(n, cols=3, rows=2, size=(3072, 2048), trim=16)
        assert box[2] <= 3072 and box[3] <= 2048
        assert box[0] >= 0 and box[1] >= 0
