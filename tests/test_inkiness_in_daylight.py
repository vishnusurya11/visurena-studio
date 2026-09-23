"""Lettering is small bright marks with hard edges, not a bright picture.

MEASURED 2026-09-22 on ep09, the series' first DAYLIGHT episode. `inkiness`
was the share of pixels over 225 times the picture's mean gradient, which is
a fine proxy while every episode is gaslight and night: nothing in ep05-ep08
is that bright except lettering. Eleven of ep09's twenty-three panels failed
it with no text on them at all -- a hazy white sky and a pale gravel path are
bright pixels, and a garden full of leaves supplies the gradient.

Raising the wall is the wrong repair: it would blind the gate to real
lettering on the night episodes, where the measure works. What separates the
two is LOCALITY. A sky is a large bright region with almost no gradient
inside it; a letter is a small bright mark with a hard edge all the way
round. So the marks are counted, not the brightness.
"""
import numpy as np

from studio.panel_dq import INK, inkiness


def smooth_sky(value: int = 245, size: int = 1024) -> np.ndarray:
    """A big, bright, featureless region -- the thing that was miscounted."""
    return np.full((size, size, 3), value, dtype=np.uint8)


def textured_daylight(size: int = 1024) -> np.ndarray:
    """A bright picture with fine texture all over it: grass, gravel, leaves."""
    rng = np.random.default_rng(7)
    base = np.full((size, size), 170, dtype=np.int16)
    base[size // 3:] += rng.integers(-35, 35, (size - size // 3, size))
    return np.repeat(np.clip(base, 0, 255).astype(np.uint8)[:, :, None], 3, axis=2)


def with_lettering(frame: np.ndarray) -> np.ndarray:
    """The same picture with a band of type struck across it.

    A caption, a label or a signboard is what the gate exists to catch, and it
    is what a model writes into a panel unasked. Type is MANY SMALL marks --
    that is what makes it type, and what makes it read differently from one
    bright opening in a wall. This band is the one measured on a real ep09
    panel, which read 0.01009 against 0.00417 for the inkiest clean panel in
    the whole series.
    """
    out = frame.copy()
    height, width, _ = out.shape
    for y in range(int(height * 0.80), int(height * 0.88), 18):
        for x in range(int(width * 0.10), int(width * 0.90), 26):
            out[y:y + 13, x:x + 16] = 255
    return out


def test_a_smooth_bright_sky_is_not_lettering():
    assert inkiness(smooth_sky()) < INK


def test_a_bright_textured_daylight_picture_is_not_lettering():
    assert inkiness(textured_daylight()) < INK


def test_lettering_on_a_daylight_picture_is_caught():
    assert inkiness(with_lettering(textured_daylight())) > INK


def test_lettering_on_a_dark_picture_is_still_caught():
    night = np.full((1024, 1024, 3), 30, dtype=np.uint8)
    assert inkiness(with_lettering(night)) > INK


def test_a_dark_picture_with_no_marks_is_clean():
    rng = np.random.default_rng(3)
    night = np.clip(np.full((1024, 1024), 30, dtype=np.int16)
                    + rng.integers(-12, 12, (1024, 1024)), 0, 255).astype(np.uint8)
    assert inkiness(np.repeat(night[:, :, None], 3, axis=2)) < INK


def test_lettering_reads_higher_than_the_same_picture_without_it():
    plain = textured_daylight()
    assert inkiness(with_lettering(plain)) > inkiness(plain) * 3


# ---- a mark is THIN; a bright hole in a dark wall is not --------------------
# MEASURED 2026-09-22 on ep09 shot 4, the medium under the railway arch: the
# bright daylight standing in the arch opening is a small bright region with a
# hard dark edge all round it, which is the description of a letter. It read
# 0.01836 against synthetic lettering at 0.01880 -- a two per cent margin,
# which is not a measurement, it is a coincidence waiting to go the other way.
# What still separates them is thickness. A stroke of type is nearly all rim;
# a hole in a wall is nearly all middle.

def bright_blob(size: int = 1024) -> np.ndarray:
    """A dark picture with one large bright opening in it -- an arch, a window."""
    out = np.full((size, size, 3), 40, dtype=np.uint8)
    out[240:800, 280:760] = 250
    return out


def test_a_bright_opening_in_a_dark_wall_is_not_lettering():
    assert inkiness(bright_blob()) < INK


def test_lettering_reads_above_a_bright_opening():
    assert inkiness(with_lettering(textured_daylight())) > inkiness(bright_blob())
