"""ep21 (2026-10-08 12:30Z): T27 (the arm reaching into the coal cellar) and
T30 (the cellar door going dark) were refused HARD as letterboxed -- 1/3 and
3/3 frames -- and QC listed them as failing takes.  The frames hold no bars:
a low-key vault fades into shadow at the top and the bottom, rows at level
5-9 with a row spread of 3.6-5.3 and no edge (the picture rises 1.5-3.3
levels past the 'band').  A bar is flat to within encoder noise, or it ends
at an edge into the picture; a shadow is neither."""
from __future__ import annotations

import numpy as np
from PIL import Image

from studio import plate_gate, take_frame

RNG = np.random.default_rng(21)


def dark_vault(size: int = 256) -> Image.Image:
    """Shadow top and bottom (level ~7, noisy), a dim picture rising gradually between."""
    rows = np.arange(size, dtype=np.float32)
    ramp = 7 + 18 * np.sin(np.pi * rows / size) ** 2          # 7 at the edges, 25 mid-frame
    grey = ramp[:, None] + RNG.normal(0, 4.2, (size, size))
    return Image.fromarray(np.clip(grey, 0, 255).astype(np.uint8)).convert("RGB")


def barred(size: int = 256, bars: int = 54, noise: float = 0.0, level: float = 0.0) -> Image.Image:
    """A picture with bars: flat (noise=0) or noisy model-drawn black with a hard edge."""
    grey = RNG.normal(70, 30, (size, size))
    grey[:bars] = level + RNG.normal(0, noise, (bars, size))
    grey[-bars:] = level + RNG.normal(0, noise, (bars, size))
    return Image.fromarray(np.clip(grey, 0, 255).astype(np.uint8)).convert("RGB")


def test_a_low_key_picture_is_not_letterboxed():
    assert not plate_gate.letterboxed(dark_vault())
    assert take_frame.row_of([dark_vault(), dark_vault(), dark_vault()]).ok


def test_flat_bars_are_still_a_letterbox():
    assert plate_gate.letterboxed(barred())


def test_noisy_bars_ending_at_an_edge_are_still_a_letterbox():
    assert plate_gate.letterboxed(barred(noise=3.5, level=4.0))


def test_a_white_padded_plate_is_still_refused():
    im = np.asarray(barred(), dtype=np.uint8).copy()
    im[:54] = 255
    im[-54:] = 255
    assert plate_gate.letterboxed(Image.fromarray(im))
