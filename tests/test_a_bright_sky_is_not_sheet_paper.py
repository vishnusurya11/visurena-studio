r"""A bright flat region that fills the whole window is the picture, not paper.

`episode_gutter.band` crops leaked sheet paper off a rendered take: bright
(mean > 190) and flat (std < 30), within MAX_FRAC = 8 % of the side. It returns
how far in the outermost such line sits.

Episode 8's palette is "bleached high-key ... bone white, alkali grey ... hard
black shadows under a white sun", and a pale desert sky at the top of a frame is
bright and flat in exactly the way sheet paper is. Q13_0E is a wide of the
plateau with the plain below, and its top 67 rows are sky at mean 198, std 2.5 --
so `band` returned its own limit, 61, and both the cell gate and the take guard
called a correct picture a gutter.

The discriminator is measured and it is clean:

    real residue   Q17_0   bottom bright rows  8..19   count 12   limit 61
                   Q17_0E  bottom bright rows  8..18   count 11
                   Q18_0   bottom bright rows  8..18   count 11
    the sky        Q13_0E  top    bright rows  0..66   count 67   limit 61

Leaked paper is a BAND: it starts near the edge and STOPS, with the picture
underneath. Sky does not stop -- it runs past the window and on into the frame.
So a run that reaches the limit is not a band, and `band` says zero.

This matters beyond the cell gate: without it the take guard would crop 61
pixels off the top of every wide desert shot in Part Two and scale the rest up,
which is a visible defect in the delivered picture rather than a repair.
"""
import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from studio import episode_gutter as eg

BOOK = ROOT / "library/20260822113400_a-study-in-scarlet"


def grey(rows=768, cols=768, seed=3):
    return np.random.default_rng(seed).normal(120, 18, (rows, cols)).clip(0, 255)


def test_a_thin_band_at_the_edge_is_still_cropped():
    a = grey()
    a[748:760] = 252.0          # 8 to 19 rows up from the bottom, like Q17_0
    assert eg.band(a, "bottom") > 0


def test_a_region_that_fills_the_window_is_the_picture():
    a = grey()
    a[:67] = 198.0              # sky, like Q13_0E
    assert eg.band(a, "top") == 0


def test_a_region_that_stops_just_inside_the_window_is_a_band():
    a = grey()
    a[:55] = 198.0
    assert eg.band(a, "top") > 0


def test_a_clean_edge_is_zero():
    assert eg.band(grey(), "top") == 0


def test_the_delivered_cells_agree_with_the_rule():
    """Every DRAWN cell of every episode on disk, after the re-cut.

    `Q*.png` only: episode 1's boards also hold `S19.prev.png`, a snapshot kept
    beside the cells rather than a cell, and it does carry a 4-pixel band --
    episode 1 is the episode the guard was calibrated on, where four takes ended
    with a white bar the owner saw at 28 s and 37 s, so a hit there is the gate
    working rather than a fault in it."""
    flagged = []
    for n in range(1, 9):
        for p in sorted((BOOK / f"episodes/ep{n:02d}/boards/cells").glob("Q*.png")):
            a = np.asarray(Image.open(p).convert("L"), dtype=float)
            if any(eg.band(a, edge) > 0 for edge in eg.EDGES):
                flagged.append(f"ep{n:02d}/{p.name}")
    if not flagged and not (BOOK / "episodes/ep08/boards/cells").exists():
        pytest.skip("the book is not on this disk")
    assert flagged == [], flagged
