"""Cells of a take sheet are pinned only where the drawer kept the camera."""
import numpy as np
from PIL import Image, ImageDraw

from studio import cell_scale as cs


def scene(scale=1.0, w=192, h=336):
    """A room: a bright window rectangle whose size follows the camera scale."""
    im = Image.new("L", (w, h), 40)
    d = ImageDraw.Draw(im)
    cx, cy, ww, wh = w // 2, h // 3, int(40 * scale), int(60 * scale)
    d.rectangle((cx - ww, cy - wh, cx + ww, cy + wh), fill=220)
    d.rectangle((10, h - int(80 * scale), w - 10, h), fill=90)
    return im


def test_scale_of_a_zoomed_copy_is_recovered():
    assert abs(cs.scale_between(scene(1.0), scene(1.2)) - 1.2) < 0.05
    assert abs(cs.scale_between(scene(1.0), scene(0.85)) - 0.85) < 0.05


def test_pins_keep_frame_zero_and_only_cells_within_tolerance_of_the_last_pin():
    scales = [1.00, 1.02, 1.03, 1.25, 1.24, 1.26, 1.04, 1.03, 1.02]
    assert cs.pins(scales, candidates=(0, 2, 4, 6, 8), tol=0.05) == [0, 2, 6, 8]


def test_a_named_push_allows_a_monotonic_gentle_ramp():
    assert cs.consistent([1.0, 0.97, 0.94, 0.90, 0.87], push=True) is True
    assert cs.consistent([1.0, 0.97, 1.05, 0.90, 0.87], push=True) is False   # not monotonic
    assert cs.consistent([1.0, 0.9, 0.8, 0.7, 0.6], push=True) is False        # travels too far
    assert cs.consistent([1.0, 1.02, 0.98, 1.03, 1.01], push=False) is True
    assert cs.consistent([1.0, 1.02, 1.25, 1.03, 1.01], push=False) is False
