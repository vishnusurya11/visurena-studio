"""A plate that fills its frame.

MEASURED building episode 11 (2026-09-16): the local plate drawer padded a
wide parlour-at-night picture into the square canvas with flat white bars
top and bottom, on two seeds running, and `frames.py` accepted both. The bars
would have been the sheet's reference and the take's own frame. A bar is a
band of rows at the top or the bottom edge that is flat (no texture) and at
one level; a thin border is not one.
"""
from __future__ import annotations

import numpy as np
from PIL import Image

BAR_MIN = 0.04
"""A band under this share of the height is a border, not a letterbox."""
FLAT_STD = 6.0
"""Standard deviation of a bar's rows: a padded band is flat; a picture is not."""


def band_depth(grey: np.ndarray, from_top: bool) -> int:
    """How many rows from that edge are flat and at the edge row's own level."""
    rows = grey if from_top else grey[::-1]
    level = float(rows[0].mean())
    depth = 0
    for row in rows:
        if row.std() > FLAT_STD or abs(float(row.mean()) - level) > FLAT_STD:
            break
        depth += 1
    return depth


def letterboxed(image: Image.Image) -> bool:
    """True when flat bands at the top AND the bottom each take BAR_MIN of the height."""
    grey = np.asarray(image.convert("L"), dtype=np.float32)
    least = int(BAR_MIN * grey.shape[0])
    return band_depth(grey, True) >= least and band_depth(grey, False) >= least
