"""A leaked gutter hugs an edge and is flat.  A lit doorway does neither.

`white_lines` rejected any row or column with `mean > 190 and std < 30`, at any
position in the cell.  It is looking for GUTTER BLEED -- a strip of the sheet's
white paper left inside a cut cell -- and a gutter residue is contiguous with a
frame edge and almost perfectly uniform.

MEASURED on episode 3's own cells, 2026-09-13:

    Q11_0.before.png   col 83  mean 215.2  std 26.9   83 px from the nearest edge
    Q23_0.png          col 74  mean 190.3  std 30.0   74 px from the nearest edge

Both are lit architecture -- a doorway jamb, a window -- 74 to 83 pixels inside
the picture, with ten times the variance of paper.

WHAT THE FALSE POSITIVE COST, traced through `seq_hall.dq.json`: the flagged
cell made the sheet unclean, which bought a $0.13 strict redraw, which
overwrote all nine hall cells, which introduced a duplicate pair the first
attempt did not have, which had `Q11_0E` deleted by `drop_end_copies`.  Shot 11
rendered with no END pin because of a fault that was never there.
"""
import importlib.util
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
FRAMES = ROOT / "library/20260822113400_a-study-in-scarlet/episodes/ep03/frames"


@pytest.fixture(scope="module")
def boards():
    spec = importlib.util.spec_from_file_location("sb", ROOT / "scripts/episode/seq_boards.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def cell(tmp_path, name: str, art: np.ndarray) -> Path:
    out = tmp_path / name
    Image.fromarray(art.astype(np.uint8), mode="L").save(out)
    return out


def picture(seed: int = 0, size: int = 200) -> np.ndarray:
    return np.random.default_rng(seed).integers(20, 140, size=(size, size))


def test_a_flat_white_strip_at_the_edge_is_still_caught(tmp_path, boards):
    """The fault this gate exists for: sheet paper left inside the cut."""
    art = picture()
    art[:, :5] = 250
    assert boards.white_lines([cell(tmp_path, "Q00_0.png", art)])


def test_a_flat_white_strip_at_the_far_edge_is_caught(tmp_path, boards):
    art = picture()
    art[:, -5:] = 250
    assert boards.white_lines([cell(tmp_path, "Q00_1.png", art)])


def test_a_flat_white_band_along_the_top_is_caught(tmp_path, boards):
    art = picture()
    art[:4, :] = 248
    assert boards.white_lines([cell(tmp_path, "Q00_2.png", art)])


def test_a_bright_TEXTURED_column_in_the_middle_is_not_a_gutter(tmp_path, boards):
    """mean 215, std 27, 83 px in -- episode 3's hall doorway, exactly."""
    art = picture()
    art[:, 83] = np.random.default_rng(7).normal(215, 27, size=art.shape[0]).clip(0, 255)
    assert boards.white_lines([cell(tmp_path, "Q11_0.png", art)]) == []


def test_a_bright_FLAT_column_in_the_middle_is_not_a_gutter_either(tmp_path, boards):
    """A gutter cannot appear in the middle of a photograph. A blown window can."""
    art = picture()
    art[:, 100] = 250
    assert boards.white_lines([cell(tmp_path, "Q11_1.png", art)]) == []


@pytest.mark.skipif(not (FRAMES / "Q23_0.png").exists(), reason="episode 3 frames not on disk")
def test_the_real_cells_that_tripped_it_are_clean(boards):
    """The two cells measured above, straight off disk."""
    names = [n for n in ("Q23_0.png", "Q11_0.before.png") if (FRAMES / n).exists()]
    assert names
    assert boards.white_lines([FRAMES / n for n in names]) == []


@pytest.mark.skipif(not FRAMES.exists(), reason="episode 3 frames not on disk")
def test_no_shipped_cell_of_episode_three_is_flagged(boards):
    """The episode went out with these cells; none of them carries sheet paper."""
    cells = sorted(p for p in FRAMES.glob("Q??_?.png"))
    assert cells
    assert boards.white_lines(cells) == []
