"""An END cell the take cannot reach by one camera move is not a destination.

MEASURED on episode 2: 9 of the 13 drawn END cells score BELOW `END_FLOOR`
against their own start cell -- Q05_0 -> Q05_0E is 0.072, Q19_1 -> Q19_1E is
-0.019.  The drawer answered "the shot ends here" by moving to a different
camera setup, which is the one thing the owner's rule forbids ("keep the
movement to simple camera movements ... to avoid the morphing").

The take is then sent from its start cell toward a picture no simple move can
travel to, and `drift` fails it for not arriving: seven hard drift failures,
every one on an aimed segment whose target is a re-staged END cell.  Failing
the take for the sheet's fault is measuring the wrong thing.  A re-staged END
cell is dropped from the reference list and from the prompt; the sheet gate is
where that fault belongs, and it is caught there now.
"""
from PIL import Image

from studio import episode_seq_board as sq


def draw(path, seed):
    """A smooth picture.  A crop of it is the same picture after a camera move; a
    different seed is a different room.  Noise would decorrelate under any crop,
    which would make the "one move away" case fail for the wrong reason."""
    import numpy as np
    y, x = np.mgrid[0:64, 0:64]
    a = 128 + 110 * np.sin((x + 3 * seed) / 11.0) * np.cos((y + 5 * seed) / 13.0)
    Image.fromarray(a.astype("uint8")).save(path)
    return path


def push(src, out):
    """The same picture after a real push in: MEASURED at 0.661, inside the band.
    A 4px crop measures 0.968, which is a COPY and no destination at all."""
    Image.open(src).crop((16, 16, 48, 48)).resize((64, 64)).save(out)
    return out


def test_a_restaged_end_pair_is_named_by_the_band():
    assert sq.end_pair_verdict(0.072) == "restaged"
    assert sq.end_pair_verdict(0.553) == "ok"
    assert sq.end_pair_verdict(0.95) == "copy"


def test_the_end_cell_is_reachable_when_it_is_one_move_away(tmp_path):
    a, b = tmp_path / "Q00_0.png", tmp_path / "Q00_0E.png"
    src = draw(a, 1)
    push(src, b)
    assert sq.reaches(a, b)


def test_a_restaged_end_cell_is_not_reachable(tmp_path):
    a, b = draw(tmp_path / "Q05_0.png", 1), draw(tmp_path / "Q05_0E.png", 99)
    assert not sq.reaches(a, b)


def test_a_missing_start_cell_is_not_reachable(tmp_path):
    b = draw(tmp_path / "Q05_0E.png", 99)
    assert not sq.reaches(tmp_path / "Q05_0.png", b)


def test_the_take_keeps_only_the_end_cells_it_can_travel_to(tmp_path):
    import sys
    sys.path.insert(0, "scripts/episode")
    import takes_r2v as tr

    frames = tmp_path / "frames"
    frames.mkdir()
    reachable = draw(frames / "Q00_0.png", 1)
    push(reachable, frames / "Q00_0E.png")
    draw(frames / "Q01_0.png", 1)
    draw(frames / "Q01_0E.png", 99)          # a re-stage
    draw(frames / "Q02_0.png", 5)            # no END cell at all
    segs = [(0, 0), (1, 0), (2, 0)]
    assert tr.end_cells(frames, segs) == [(0, 0)]


# ---- a COPY is not a destination either -------------------------------------

def test_a_copy_end_cell_is_not_a_destination(tmp_path):
    """MEASURED, three ways, on the same 9 cells of episode 2:

      sheet prose ("a DIFFERENT photograph")      -> RE-STAGED, 0.072-0.406
      + the start cell as a reference image       -> COPY, 0.984-0.997
      + prose demoting the reference to the angle -> COPY, 0.981

    With a dominant reference image the drawer copies it; without one it
    re-stages.  Neither lands in the band, so the honest reading is that this
    drawer cannot be asked for "the same shot one moment later" at all.

    Aiming a take at a COPY is worse than aiming it at nothing: it tells the
    take to end where it began, which is the stillness the owner banned
    outright ("do not do any slow shots .. strict rule").  With no END cell the
    take follows the motion described in words, and `drift` has no aimed
    segment to fail.  So only a cell inside the BAND is a destination."""
    a = draw(tmp_path / "Q05_0.png", 1)
    import shutil
    b = tmp_path / "Q05_0E.png"
    shutil.copy(a, b)
    assert sq.end_pair_verdict(1.0) == "copy"
    assert not sq.reaches(a, b)
