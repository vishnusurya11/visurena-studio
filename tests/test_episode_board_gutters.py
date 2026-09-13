"""The sheet's gutters are FOUND, not assumed at thirds."""
import numpy as np

from studio import episode_board as board


def sheet(h=300, w=210, gutters_y=((96, 104), (204, 212)), gutters_x=((66, 72), (140, 146))):
    """A dark textured sheet with paper-white gutters where the drawer put them."""
    rng = np.random.default_rng(1)
    grey = rng.uniform(20, 120, (h, w))
    for a, b in gutters_y:
        grey[a:b, :] = 250
    for a, b in gutters_x:
        grey[:, a:b] = 250
    return grey


def test_bands_finds_the_drawn_gutters_not_the_thirds():
    assert board.bands(sheet(), axis=0) == [(96, 104), (204, 212)]
    assert board.bands(sheet(), axis=1) == [(66, 72), (140, 146)]


def test_a_bright_textured_stripe_is_not_a_gutter():
    g = sheet()
    g[150:160, :] = np.random.default_rng(2).uniform(60, 255, (10, 210))
    assert board.bands(g, axis=0) == [(96, 104), (204, 212)]


def test_cells_are_the_regions_between_the_gutters():
    boxes = board.cell_boxes(sheet())
    assert len(boxes) == 9
    assert boxes[0] == (0, 0, 66, 96)
    assert boxes[4] == (72, 104, 140, 204)
    assert boxes[8] == (146, 212, 210, 300)


def test_a_sheet_without_two_gutters_per_axis_falls_back_to_thirds():
    g = sheet(gutters_y=(), gutters_x=())
    assert board.cell_boxes(g) == [board.panel_box(i, (210, 300)) for i in range(9)]
