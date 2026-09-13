"""The DQ aims a segment only at an END cell the take was actually GIVEN.

`segments_of` used to target any `Q..E.png` that existed on disk.  That was
right while every drawn END cell was also staged as a reference, and became
wrong the moment `takes_r2v.end_cells` started dropping the ones no camera move
can reach: the take is never shown the picture, and is then failed by `drift`
for not arriving at it.

MEASURED on episode 2 iteration 3: nine re-staged END cells were dropped from
the reference list, and drift still failed T00 (0.37), T05 (-0.09) and T07
(0.10) -- against Q00_0E, Q05_0E and Q07_0E, the exact three cells the take
never received.  The judge has to use the rule the builder uses.
"""
from PIL import Image

from studio import episode_seq_board as sq
from studio.take_verdict import segments_of


def draw(path, seed=1):
    import numpy as np
    y, x = np.mgrid[0:64, 0:64]
    a = 128 + 110 * np.sin((x + 3 * seed) / 11.0) * np.cos((y + 5 * seed) / 13.0)
    Image.fromarray(a.astype("uint8")).save(path)
    return path


def push(src, out):
    """A real push in: MEASURED 0.66, inside the 0.45-0.80 band."""
    Image.open(src).crop((16, 16, 48, 48)).resize((64, 64)).save(out)
    return out


ANCHORS = [["Q00_0.png", 0], ["Q00_1.png", 48]]


def test_a_reachable_end_cell_is_the_target(tmp_path):
    push(draw(tmp_path / "Q00_0.png"), tmp_path / "Q00_0E.png")
    draw(tmp_path / "Q00_1.png", 2)
    segs = segments_of(ANCHORS, tmp_path, 4.0)
    assert segs[0][1] == "Q00_0E.png"


def test_a_restaged_end_cell_is_not_the_target(tmp_path):
    """It was never staged as a reference, so arriving at it was never asked for."""
    draw(tmp_path / "Q00_0.png", 1)
    draw(tmp_path / "Q00_0E.png", 99)          # a re-stage
    draw(tmp_path / "Q00_1.png", 2)
    segs = segments_of(ANCHORS, tmp_path, 4.0)
    assert segs[0][1] == "Q00_0.png"           # aims at itself: no target, drift cannot fail hard


def test_a_copy_end_cell_is_not_the_target(tmp_path):
    import shutil
    draw(tmp_path / "Q00_0.png", 1)
    shutil.copy(tmp_path / "Q00_0.png", tmp_path / "Q00_0E.png")
    draw(tmp_path / "Q00_1.png", 2)
    assert segments_of(ANCHORS, tmp_path, 4.0)[0][1] == "Q00_0.png"


def test_no_end_cell_at_all_still_aims_at_itself(tmp_path):
    draw(tmp_path / "Q00_0.png", 1)
    draw(tmp_path / "Q00_1.png", 2)
    assert segments_of(ANCHORS, tmp_path, 4.0)[0][1] == "Q00_0.png"


def test_the_judge_and_the_builder_agree(tmp_path):
    """The one invariant: whatever `end_cells` stages, `segments_of` aims at."""
    import sys
    sys.path.insert(0, "scripts/episode")
    import takes_r2v as tr

    push(draw(tmp_path / "Q00_0.png"), tmp_path / "Q00_0E.png")   # reachable
    draw(tmp_path / "Q00_1.png", 2)
    draw(tmp_path / "Q00_1E.png", 99)                             # re-staged
    staged = {sq.cell_name(a, b, end=True) for a, b in tr.end_cells(tmp_path, [(0, 0), (0, 1)])}
    aimed = {t for _c, t, *_ in segments_of(ANCHORS, tmp_path, 4.0) if t.endswith("E.png")}
    assert staged == aimed == {"Q00_0E.png"}


# ---- the record is the truth, not the disk ---------------------------------

def test_the_take_s_OWN_RECORD_decides_what_it_was_aimed_at(tmp_path):
    """MEASURED 2026-09-13, and this is the SECOND time this fault appeared.

    `takes_r2v --no-ends` withheld every END picture; `segments_of` went on
    reading DISK, found the cells still sitting there, and aimed the takes at
    them. T08 staged no END picture and was hard-failed on drift for not
    reaching Q08_0E; T11 the same for Q11_1E. Both were measurement artefacts.

    Disk says what was DRAWN. The take's record says what it was GIVEN. Only the
    second one can judge it."""
    push(draw(tmp_path / "Q00_0.png"), tmp_path / "Q00_0E.png")   # reachable, on disk
    draw(tmp_path / "Q00_1.png", 2)

    # no record given: disk decides, as before
    assert segments_of(ANCHORS, tmp_path, 4.0)[0][1] == "Q00_0E.png"

    # a record that staged it: aimed
    assert segments_of(ANCHORS, tmp_path, 4.0, staged=["Q00_0E.png"])[0][1] == "Q00_0E.png"

    # a record that did NOT stage it: not aimed, however reachable it looks
    assert segments_of(ANCHORS, tmp_path, 4.0, staged=[])[0][1] == "Q00_0.png"
    assert segments_of(ANCHORS, tmp_path, 4.0, staged=["char-x.png", "Q00_0.png"])[0][1] == "Q00_0.png"
