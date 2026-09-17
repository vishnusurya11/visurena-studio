"""A plate that comes back letterboxed is refused and re-rolled.

MEASURED building episode 11 (2026-09-16): the local plate drawer padded a
wide parlour-at-night picture into the square canvas with white bars top and
bottom, twice on two seeds, and `frames.py` accepted it both times -- the
gate that did not exist. The bars would have been the storyboard's reference
and the sheet's own frame.
"""
from pathlib import Path

import numpy as np
from PIL import Image

from studio import plate_gate


def picture(bars: int, w: int = 256, h: int = 256, level: int = 255) -> Image.Image:
    rng = np.random.default_rng(7)
    a = rng.integers(20, 200, (h, w, 3), dtype=np.uint8)
    if bars:
        a[:bars, :, :] = level
        a[-bars:, :, :] = level
    return Image.fromarray(a, "RGB")


def test_white_bars_top_and_bottom_are_letterboxing():
    assert plate_gate.letterboxed(picture(bars=40))
    assert plate_gate.letterboxed(picture(bars=40, level=0)), "black bars are bars too"


def test_a_full_picture_is_not():
    assert not plate_gate.letterboxed(picture(bars=0))
    assert not plate_gate.letterboxed(picture(bars=3)), "a thin border is not a letterbox"


def test_the_plate_is_re_rolled_on_the_next_seed_until_it_fills_the_frame(tmp_path):
    import sys

    sys.path.insert(0, "scripts/episode")
    import frames

    seeds = []

    def draw(seed: int) -> Path:
        seeds.append(seed)
        p = tmp_path / f"raw_{seed}.png"
        picture(bars=40 if len(seeds) < 3 else 0).save(p)
        return p

    out = frames.plate_rolled(draw, tmp_path / "plate.png", seed=100)
    assert out.exists() and not plate_gate.letterboxed(Image.open(out))
    assert seeds == [100, 100 + frames.ROLL_STEP, 100 + 2 * frames.ROLL_STEP]
    assert (tmp_path / "rejected" / "plate.bars1.png").exists()


def test_three_letterboxed_rolls_stop_the_run(tmp_path):
    import sys

    sys.path.insert(0, "scripts/episode")
    import frames
    import pytest

    def draw(seed: int) -> Path:
        p = tmp_path / f"raw_{seed}.png"
        picture(bars=40).save(p)
        return p

    with pytest.raises(SystemExit):
        frames.plate_rolled(draw, tmp_path / "plate.png", seed=100)
