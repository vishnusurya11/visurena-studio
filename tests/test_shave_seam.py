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
