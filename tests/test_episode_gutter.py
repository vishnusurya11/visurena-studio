import numpy as np

from studio import episode_gutter as g


def frame(h=400, w=60, level=80):
    return np.full((h, w), float(level))


def test_a_clean_frame_cuts_nothing():
    assert g.band(frame(), "bottom") == 0
    assert g.band(frame(), "top") == 0
    assert g.band(frame(), "left") == 0


def test_a_paper_white_band_is_cut_with_the_grey_cell_below_it():
    f = frame()
    f[-8:] = 245           # paper-white gutter at the very bottom
    f[-14:-8] = 150        # the next storyboard cell showing under it
    f[-20:-14] = 240       # a second white line further up
    assert g.band(f, "bottom") == 20 + g.MARGIN


def test_a_bright_wall_is_not_a_gutter():
    f = frame()
    f[-8:] = np.random.default_rng(0).uniform(100, 255, (8, 60))  # textured, high std
    assert g.band(f, "bottom") == 0


def test_the_band_never_exceeds_the_ceiling():
    f = frame()
    f[-60:] = 250
    assert g.band(f, "bottom") == round(400 * g.MAX_FRAC)


def test_the_box_takes_the_widest_band_over_all_frames():
    a, b = frame(), frame()
    a[-6:] = 250
    b[:4, :] = 250
    assert g.box([a, b]) == (0, 4 + g.MARGIN, 60, 400 - 6 - g.MARGIN)


def test_a_box_that_cuts_nothing_needs_no_filter():
    assert g.crop_filter((0, 0, 60, 100), 60, 100) == ""
    assert g.crop_filter((0, 6, 60, 92), 60, 100) == "crop=60:86:0:6"
