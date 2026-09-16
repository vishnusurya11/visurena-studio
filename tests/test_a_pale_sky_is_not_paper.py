"""Leaked sheet paper is FLAT. A pale sky is bright but it has weather in it.

MEASURED building episode 9. `Q00_0` and `Q01_0` are wides of the valley of Utah
at sunrise and open on a bleached sky: the top 50 and 16 rows read mean 203 and
200 at std 16.9 and 13.5. `episode_gutter.FLAT` was 30.0, so both were called
leaked gutter, and the cost of that one false positive was:

    the sheet DQ failed a setup whose four pictures were correct
    a $0.13 STRICT redraw was bought and produced the same reading
    the take guard cropped 52 and 51 px off the top of T00 and T01 --
        real picture, removed from the delivered episode
    the EDIT gate then failed the whole master, because a cropped segment
        no longer matches the take it was cut from

`found >= limit` already covers the OTHER sky case, where the bright flat region
fills the window and runs on into the frame (episode 8's Q13_0E, 67 rows at std
2.5). It cannot cover this one: this sky STOPS at row 50, where the mountains
begin, so by shape it is indistinguishable from a band. What separates them is
flatness, and the two populations do not overlap:

    real leaked paper       std 2-5     (episode 3's residues, measured)
    episode 9's pale sky    std 13.5, 16.9
    every band found across every cell of every episode on disk: those two

So the floor goes to 8.0 -- above every paper reading this repo has ever
recorded, below every sky reading. Same fault as `house_style` and the stale
read-back: a constant calibrated on a world that has since changed. 30.0 was set
for soot-black gaslit London, and Part Two is a bleached desert.
"""
import numpy as np
import pytest

from studio import episode_gutter as g


def sky(rows: int = 50, std: float = 15.0, side: int = 768) -> np.ndarray:
    """A bright band with weather in it, over a dark picture."""
    rng = np.random.default_rng(7)
    frame = np.full((side, side), 60.0)
    frame[:rows] = 203.0 + rng.normal(0, std, (rows, side))
    return frame


def paper(rows: int = 12, side: int = 768) -> np.ndarray:
    """A leaked gutter: bright, and flat the way printed paper is."""
    rng = np.random.default_rng(7)
    frame = np.full((side, side), 60.0)
    frame[:rows] = 250.0 + rng.normal(0, 3.0, (rows, side))
    return frame


def test_a_pale_sky_that_stops_is_still_sky():
    assert g.band(sky(), "top") == 0


def test_a_shallow_pale_sky_is_sky_too():
    """`Q01_0` is only 16 rows deep -- shallower than some real residues."""
    assert g.band(sky(rows=16, std=13.5), "top") == 0


def test_leaked_paper_is_still_cropped():
    cut = g.band(paper(), "top")
    assert cut >= 12, "a real gutter residue must still be found"


def test_a_thin_residue_is_still_cropped():
    """Episode 8's three real residues ran 11 to 12 rows."""
    assert g.band(paper(rows=11), "top") >= 11


def test_the_floor_sits_between_the_two_populations():
    """Stated as a number so a future loosening has to argue with the measurement:
    paper reads 2-5, the skies that cost episode 9 a redraw read 13.5 and 16.9."""
    assert 5.0 < g.FLAT < 13.5


@pytest.mark.parametrize("edge", ["top", "bottom", "left", "right"])
def test_every_edge_reads_the_same_way(edge):
    frame = sky()
    if edge in ("bottom", "right"):
        frame = frame[::-1] if edge == "bottom" else frame.T[::-1].T
    elif edge == "left":
        frame = frame.T
    assert g.band(frame, edge) == 0


# ---- a band is CONTIGUOUS with the edge it leaked from ----------------------

def noisy_sky(side: int = 768) -> np.ndarray:
    """A pale sky whose flatness straddles the floor, over a picture.

    MEASURED on episode 9's T09, the mule train on the hazy high road: rows 0-2
    read std 6.9, row 8 reads 8.4, row 31 reads 8.2, row 41 reads 8.0 -- in and
    out of the floor all the way down. `band` took the OUTERMOST qualifying row
    as the depth, so a sky that qualifies on scattered rows produced a 53-pixel
    "band" with picture in the middle of it, and `found >= limit` never fired
    because the scatter never filled the window.

    Leaked paper is a physical strip: it is contiguous with the edge, and it
    stops. So the depth is the contiguous run, never the outermost hit."""
    rng = np.random.default_rng(3)
    frame = np.full((side, side), 60.0)
    for row in range(62):
        std = 6.9 if row % 7 else 12.0          # in and out of the floor
        frame[row] = 195.0 + rng.normal(0, std, side)
    return frame


def test_a_sky_that_qualifies_on_scattered_rows_is_not_a_band():
    assert g.band(noisy_sky(), "top") == 0


# A paper strip lying over a PALE SKY is deliberately not asserted here. It has
# never occurred -- every residue on disk lies over a picture -- and the two
# rules that catch this episode's skies would read it as sky. Inventing a
# behaviour for a case nobody has measured is how the loose FLAT got here.


# ---- paper has PICTURE under it; sky has more sky --------------------------

def deep_sky(side: int = 768) -> np.ndarray:
    """The last sky that fooled the guard, and the one contiguity could not.

    MEASURED on episode 9's T06 and T09: a contiguous bright flat run of 46 and
    60 rows -- inside the 61-pixel window, so it is a band by depth, and solid,
    so it is a band by shape. What gives it away is WHERE IT STOPS. Row 46 reads
    mean 214 and row 60 reads mean 206: the run ends at BRIGHTER sky, not at a
    picture. Leaked paper is the brightest thing in the frame and the scene
    beneath it is darker by a hundred grey levels."""
    rng = np.random.default_rng(11)
    frame = np.full((side, side), 60.0)
    frame[:60] = 196.0 + rng.normal(0, 6.0, (60, side))
    frame[60:120] = 208.0 + rng.normal(0, 9.0, (60, side))   # brighter sky below
    return frame


def test_a_run_that_ends_at_brighter_sky_is_not_paper():
    assert g.band(deep_sky(), "top") == 0


def test_paper_over_a_dark_picture_is_still_cropped():
    """The case the guard exists for: episode 1's white bar, paper over scene."""
    rng = np.random.default_rng(11)
    frame = np.full((768, 768), 70.0) + rng.normal(0, 25.0, (768, 768))
    frame[:12] = 250.0
    assert g.band(frame, "top") >= 12
