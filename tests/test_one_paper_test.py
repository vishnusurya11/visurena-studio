"""One fact about paper, one function.

THREE places decided whether a bright flat run is sheet paper. Two were
recalibrated on 2026-09-16 for Part Two's pale skies (`episode_gutter.band`:
FLAT 30 -> 8 plus DROP; `episode_board.bands` asks it for its numbers). The
third, `storyboard.strip_white_edges` -- WHITE=170, mean only, no flatness, no
drop, a 6 % cap -- was missed, and it trims picture off any first frame whose
edge is sky or sand.

MEASURED (`docs/analysis/ep08_ep09_why_worse.md`, cause 7): first-frame cells
that lost 30 px or more on an edge, ep04-07 0 / 0 / 0 / 1, ep08 11 of 30, ep09
10 of 30, every one to the cap, then re-squared by centre crop (-7 % on both
axes, upscale 1.21-1.28x instead of 1.13x). Q00_0 lost its snow peaks.

So `strip_white_edges` now asks `episode_gutter.band` for every edge and owns
no number of its own.
"""
import importlib.util
import sys
from pathlib import Path

import numpy as np
from PIL import Image

from studio import episode_gutter as gutter

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("ep_storyboard_paper",
                                               ROOT / "scripts" / "episode" / "storyboard.py")
sb = importlib.util.module_from_spec(_spec)
sys.modules["ep_storyboard_paper"] = sb
_spec.loader.exec_module(sb)


def frame(top_rows: int, mean: float, std: float, side: int = 768, seed: int = 7) -> Image.Image:
    """A dark textured picture with `top_rows` of something bright along the top."""
    rng = np.random.default_rng(seed)
    grey = np.full((side, side), 60.0) + rng.normal(0, 20.0, (side, side))
    grey[:top_rows] = mean + rng.normal(0, std, (top_rows, side))
    return Image.fromarray(np.clip(grey, 0, 255).astype(np.uint8), "L").convert("RGB")


def test_a_pale_sky_top_edge_is_not_trimmed():
    """Bright (mean 200) but with weather in it (std 15): sky, kept whole."""
    sky = frame(40, 200.0, 15.0)
    assert sb.strip_white_edges(sky).size == sky.size


def test_a_paper_strip_over_a_dark_picture_is_trimmed():
    """Bright (250) and flat (std 2) over a picture a hundred levels darker."""
    paper = frame(12, 250.0, 2.0)
    trimmed = sb.strip_white_edges(paper)
    assert trimmed.size[0] == paper.size[0]
    assert paper.size[1] - trimmed.size[1] >= 12


def test_the_valley_of_utah_at_sunrise_loses_no_rows():
    """The synthetic that mirrors ep09's Q00_0: 50 rows of sky at mean 203,
    std 16.9, over mountains. `strip_white_edges` used to take the 6 % cap."""
    q00 = frame(50, 203.0, 16.9)
    assert sb.strip_white_edges(q00).size == q00.size


def test_it_asks_the_guard_and_owns_no_number_of_its_own():
    """The old constants are gone: WHITE and MAX_TRIM were the third opinion."""
    assert not hasattr(sb, "WHITE") and not hasattr(sb, "MAX_TRIM")
    grey = np.asarray(frame(12, 250.0, 2.0).convert("L"), dtype=float)
    expected = gutter.box([grey])
    trimmed = sb.strip_white_edges(frame(12, 250.0, 2.0))
    assert trimmed.size == (expected[2] - expected[0], expected[3] - expected[1])


def test_every_edge_is_asked():
    """Paper on the right edge is cut by the same rule as paper on the top."""
    rng = np.random.default_rng(3)
    grey = np.full((600, 600), 60.0) + rng.normal(0, 20.0, (600, 600))
    grey[:, -12:] = 250.0
    picture = Image.fromarray(np.clip(grey, 0, 255).astype(np.uint8), "L").convert("RGB")
    trimmed = sb.strip_white_edges(picture)
    assert trimmed.size[1] == 600 and 600 - trimmed.size[0] >= 12
