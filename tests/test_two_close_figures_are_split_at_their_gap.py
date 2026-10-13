"""Two figures standing close are two figures, not one with a dip in it.

Jekyll Hyde base sheet redraw (2026-10-13): the front and three-quarter poses
stood 20 px apart on a 1776-px sheet -- a clean backdrop gap (column spread 6.1
against the 15.0 backdrop line) but narrower than GAP_MIN (26 px), so `runs`
bridged it as "a dip inside one figure" and sheet_front.png held TWO Hydes at
0.39 of the sheet: the ep16 duplicate-character fault, waiting for a grid.
A bridged run wider than any one figure is split at its first real gap.
"""
from __future__ import annotations

import numpy as np
from PIL import Image

from studio.sheet_front import first_figure_box


def sheet(xs: list[tuple[int, int]], w: int = 1000) -> np.ndarray:
    rng = np.random.default_rng(11)
    a = np.full((300, w, 3), 128, np.uint8)
    for x0, x1 in xs:
        a[30:290, x0:x1] = rng.integers(20, 230, (260, x1 - x0, 3), dtype=np.uint8)
    return a


def test_two_figures_a_narrow_gap_apart_give_the_first():
    left, right = first_figure_box(sheet([(40, 200), (212, 372), (500, 660)]))
    assert right <= 212 + 20 + 5, (left, right)          # figure 1 and its margin, never figure 2
    assert right - left < 250
    assert right >= 200


def test_one_figure_with_a_narrow_dip_stays_whole():
    left, right = first_figure_box(sheet([(40, 110), (118, 200), (500, 660)]))
    assert right >= 200                                  # 0.16 wide: one figure, dip bridged


def test_a_wide_run_with_no_gap_inside_is_left_as_it_was():
    """Only a real backdrop gap splits; overlap with none is MAX_SHARE's business, unchanged."""
    left, right = first_figure_box(sheet([(20, 420)]))
    assert left <= 20 and right >= 420
