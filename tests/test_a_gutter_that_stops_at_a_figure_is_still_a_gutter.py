"""Two pictures stacked in one panel show a pale, even gutter line.  Measured
over the full width, a figure standing across the gutter breaks the line and
the panel passed.  Scored by thirds, a gutter that runs clean through two of
three thirds is still a gutter."""
import numpy as np

from studio import panel_dq


def _stacked(figure: bool) -> np.ndarray:
    rng = np.random.default_rng(5)
    top = rng.integers(70, 110, (256, 512, 3), dtype=np.uint8)
    bottom = rng.integers(130, 170, (256, 512, 3), dtype=np.uint8)
    frame = np.vstack([top, bottom])
    frame[253:259, :, :] = 235                       # the gutter, pale and even
    if figure:
        frame[120:420, 200:312, :] = 40              # a dark figure across the middle third
    return frame


def test_a_gutter_that_stops_at_a_figure_is_still_a_gutter():
    assert panel_dq.stacked(_stacked(figure=True)) > panel_dq.STACKED


def test_an_unbroken_gutter_still_reads():
    assert panel_dq.stacked(_stacked(figure=False)) > panel_dq.STACKED


def test_a_picture_without_a_gutter_reads_low():
    rng = np.random.default_rng(9)
    plain = rng.integers(60, 180, (512, 512, 3), dtype=np.uint8)
    assert panel_dq.stacked(plain) < 0.5
