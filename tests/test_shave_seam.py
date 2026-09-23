"""A panel's white gutter is a picture element, so it is measured off, not
guessed off.

MEASURED 2026-09-22 on ep09 shot 18: the panel came out of its grid with a
pale seam along the top and right edges, and the ink gate caught it -- bright,
hard-edged marks standing clear of a dark picture, which is exactly what the
gate is for. `panel_box` sheds a FIXED 16 pixels, which was enough for the
grids drawn so far and is not enough for these.

A fixed trim is a guess about a number the picture already knows. The seam is
whatever edge rows and columns are near-uniform and much paler than the
picture inside them, so that is what comes off.
"""
import numpy as np

from studio.storyboard_grid import seam_box


def picture(size: int = 128, value: int = 60) -> np.ndarray:
    rng = np.random.default_rng(5)
    body = np.clip(np.full((size, size), value, dtype=np.int16)
                   + rng.integers(-20, 20, (size, size)), 0, 255).astype(np.uint8)
    return np.repeat(body[:, :, None], 3, axis=2)


def framed(frame: np.ndarray, width: int, value: int = 250) -> np.ndarray:
    out = frame.copy()
    out[:width, :] = value
    out[-width:, :] = value
    out[:, :width] = value
    out[:, -width:] = value
    return out


def test_a_picture_with_no_seam_is_left_alone():
    assert seam_box(picture()) == (0, 0, 128, 128)


def test_a_seam_on_every_side_comes_off():
    assert seam_box(framed(picture(), 6)) == (6, 6, 122, 122)


def test_a_seam_on_two_sides_only_comes_off_those_sides():
    frame = picture()
    frame[:5, :] = 250
    frame[:, -9:] = 250
    assert seam_box(frame) == (0, 5, 119, 128)


def test_a_wide_seam_comes_off_whole():
    assert seam_box(framed(picture(), 20)) == (20, 20, 108, 108)


def test_a_pale_picture_is_not_all_seam():
    left, top, right, bottom = seam_box(picture(value=210))
    assert (right - left, bottom - top) == (128, 128)


def test_a_seam_is_never_allowed_to_eat_the_picture():
    all_white = np.full((128, 128, 3), 252, dtype=np.uint8)
    left, top, right, bottom = seam_box(all_white)
    assert right - left > 0 and bottom - top > 0


def test_a_gutter_inside_the_edge_takes_the_neighbours_spill_with_it():
    """ep09 lawn 3x1: the model drew its middle panel narrower than its cell,
    so shot 14 came out with 93 columns of the left panel, a 7-column white
    gutter, and then its own picture. The gutter is thin and has picture on
    both sides; everything outside it is the neighbour's."""
    frame = picture(200)
    frame[:, 30:36] = 250
    assert seam_box(frame)[0] == 36


def test_a_broad_pale_band_inside_the_picture_is_not_a_gutter():
    frame = picture(200)
    frame[:, 20:48] = 250           # a white wall, 28 columns: wider than any gutter
    assert seam_box(frame)[0] == 0


def test_a_pale_graded_sky_is_never_taken_for_a_gutter():
    """The first cut of the inner-gutter rule shaved 98-166 rows of morning sky
    off ep09 shots 1-3: rows of a sky that grades across the pale threshold
    make thin 'seam' runs with sky on both sides. A gutter has darker picture
    on both sides of it."""
    frame = picture(200, value=60)
    for r in range(60):
        frame[r, :] = 228 + (r % 3) * 5          # 228 / 233 / 238: sky flickering across the line
    assert seam_box(frame)[1] == 0


def test_a_deep_pale_sky_at_the_edge_is_picture():
    """ep09 superseded garden 2x2 slot 3: rows 0-259 of hazy sky at mean 236-238,
    std under 1, all counted as seam; 248 rows were cut (grid-stage audit)."""
    frame = picture(992)
    frame[:260, :] = 237
    assert seam_box(frame)[1] == 0


def test_a_white_rail_across_the_picture_is_not_a_gutter():
    """A 10-px white rail at row 150 cut 160 rows of picture (grid-stage audit):
    ep09's garden has a white paling rail running edge to edge."""
    frame = picture(992)
    frame[150:160, :] = 250
    assert seam_box(frame)[1] == 0
