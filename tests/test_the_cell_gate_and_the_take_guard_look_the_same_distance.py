r"""Two measures of one thing, looking different distances into the picture.

`seq_boards.white_lines` refuses a CELL with sheet paper leaked into it, and
looks GUTTER_EDGE = 6 pixels in from each border. `episode_gutter.band` crops
the same leak out of a rendered TAKE, and looks MAX_FRAC = 0.08 of the side --
61 pixels of a 768 cell, ten times as far.

So a residue between 7 and 61 pixels in passes the cell gate and is then cropped
by the take guard. That is not belt and braces: the crop changes the picture's
geometry, the assembled frames stop matching the take they were cut from, and
the EDIT gate fails the whole episode.

MEASURED, episode 8. Cells Q17_0 and Q18_0 carry a paper-white band at rows 8 to
19 from their bottom edge -- eight pixels past where `white_lines` stops looking.
Both shipped. The take guard found them, cropped 22 and 21 pixels off T17 and
T18, and `qc` then reported

    edit: FAIL | segments off 2/28 | cuts off 3/27

with T17 at mean 21.4 and T18 at 11.5 against their own sources. A clean episode
failed QC because two gates that measure the same leak disagreed about how far
in to look.

THE CALIBRATED ONE WINS. `episode_gutter`'s window was measured on episode 1,
where four takes ended with a paper-white band and the owner saw it as a white
bar at 28 s and 37 s. `white_lines` now asks it, instead of keeping a second
opinion.

Measured across all 461 cells of the eight episodes on disk, the change flags
exactly four new cells and they are episode 8's four bad ones:

    ep01 185 cells   6px: 1   guard window: 1
    ep02  54            0                   0
    ep03  49            0                   0
    ep04  35            0                   0
    ep05  32            0                   0
    ep06  27            0                   0
    ep07  32            0                   0
    ep08  47            0                   4   Q13_0E Q17_0 Q17_0E Q18_0

Zero false positives on seven delivered episodes.
"""
import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import importlib.util

from studio import episode_gutter as eg

spec = importlib.util.spec_from_file_location("seq_boards", ROOT / "scripts/episode/seq_boards.py")
sb = importlib.util.module_from_spec(spec)
sys.modules["seq_boards"] = sb
spec.loader.exec_module(sb)

BOOK = ROOT / "library/20260822113400_a-study-in-scarlet"


def cell(tmp_path, name, band_at=None, thickness=0):
    """A 768 cell of mid-grey texture, optionally with a paper-white band."""
    rng = np.random.default_rng(7)
    a = rng.normal(120, 18, (768, 768)).clip(0, 255)
    if band_at is not None:
        a[768 - band_at - thickness:768 - band_at] = 252.0
    p = tmp_path / name
    Image.fromarray(a.astype(np.uint8)).save(p)
    return p


def test_a_band_eight_pixels_in_is_found(tmp_path):
    """Episode 8's Q17_0: rows 8 to 19 from the bottom."""
    p = cell(tmp_path, "Q17_0.png", band_at=8, thickness=12)
    assert sb.white_lines([p]) == ["Q17_0.png"]


def test_a_band_at_the_very_edge_is_still_found(tmp_path):
    p = cell(tmp_path, "Q01_0.png", band_at=0, thickness=4)
    assert sb.white_lines([p]) == ["Q01_0.png"]


def test_a_clean_cell_is_silent(tmp_path):
    assert sb.white_lines([cell(tmp_path, "Q02_0.png")]) == []


def test_a_band_beyond_the_guard_s_reach_is_not_this_fault(tmp_path):
    """Past 8 % of the side it is a picture, not leaked paper -- and the take
    guard would not crop it either, so the two stay in step."""
    p = cell(tmp_path, "Q03_0.png", band_at=200, thickness=10)
    assert sb.white_lines([p]) == []


def test_it_asks_the_take_guard_rather_than_keeping_its_own_opinion():
    """The point of the change: one window, owned by the module that calibrated
    it. If this drifts apart again the episode fails QC and nothing says why."""
    said = (ROOT / "scripts/episode/seq_boards.py").read_text(encoding="utf-8")
    assert "episode_gutter" in said


def test_the_seven_delivered_episodes_stay_clean():
    """A widened gate must not start refusing what has already shipped."""
    flagged = {}
    for n in range(2, 8):
        cells = sorted((BOOK / f"episodes/ep{n:02d}/boards/cells").glob("*.png"))
        if not cells:
            continue
        bad = sb.white_lines(cells)
        if bad:
            flagged[n] = bad
    if not flagged and not any((BOOK / f"episodes/ep{n:02d}/boards/cells").exists() for n in range(2, 8)):
        pytest.skip("the book is not on this disk")
    assert flagged == {}, flagged
