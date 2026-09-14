"""A whole-frame score measures the FRAME; an END cell's job is a changed SUBJECT.

`END_CEILING` calls a pair a "copy" over 0.80, on the reasoning that two nearly
identical pictures mean nothing moved.  That holds when the camera moves.  It
fails on a LOCKED-OFF camera, where most of the frame is supposed to be
identical and the change is confined to one part of it.

Episode 4's shot 21: the same room, the same table, the same Rance in the
foreground, and in the END cell the two men have turned and are walking out
through the door.  It scores 0.856, was called a copy, and the take was given no
destination -- so at frame 128 it invented one, cutting to
plate_rance_parlour.png and reproducing it at 0.999 for 47 frames.  Three rolls
did the same thing.

Read in blocks (7 x 4 over the thumbnail) the pairs separate with nothing in
between -- blocks scoring under 0.2, measured over all eleven of episode 4's END
pairs:

    Q08_0 0.982 global   0 blocks   a copy, and it looks like one
    Q00_0 0.935          0          a copy
    Q11_0 0.945          0          Rance tilts his head; a copy
    Q15_0 0.938          4          Rance leans in and re-gestures -- NOT a copy
    Q21_0 0.856          3          the two men walk out -- NOT a copy
    Q20_0 0.856          3
    Q09_0 0.807          3

Verified by eye on Q21, Q15 (kept) and Q11, Q08 (still copies).  So one block of
real change is enough, and the ceiling only stands when there is none.

This is the same error as the insert floor (cf167b8), at the other end of the
band: there the subject fills the frame so a LOW score meant the subject moved;
here the subject is a small part of it so a HIGH score means the room did not.

Note what this changes and what it does not.  It changes which REFERENCE a take
is given.  The foreign gate that failed T21 is untouched, and T21 must still
render again and pass it.
"""
import numpy as np
import pytest
from PIL import Image

from studio.episode_seq_board import BLOCK_FLOOR, changed_blocks, end_pair_verdict


def cell(rows: int = 84, cols: int = 48, seed: int = 0) -> Image.Image:
    return Image.fromarray(np.random.RandomState(seed).randint(0, 255, (rows, cols), dtype=np.uint8))


def with_patch(base: Image.Image, seed: int = 9) -> Image.Image:
    """The same picture with one BLOCK replaced -- a doorway that emptied.

    The patch is aligned to the 7 x 4 grid on purpose.  A region straddling two
    blocks changes half of each, which reads around 0.5 and is not a changed
    block -- which is the point of reading in blocks at all: a change has to be
    somewhere, not smeared."""
    a = np.asarray(base).copy()
    a[12:24, 12:24] = np.random.RandomState(seed).randint(0, 255, (12, 12), dtype=np.uint8)
    return Image.fromarray(a)


def test_a_picture_against_itself_has_no_changed_block():
    a = cell()
    assert changed_blocks(a, a) == 0


def test_one_replaced_region_is_a_changed_block():
    a = cell()
    assert changed_blocks(a, with_patch(a)) >= 1


def test_a_high_scoring_pair_with_a_changed_block_is_not_a_copy():
    """Q21_0: 0.856 global, the two men walk out of the doorway."""
    assert end_pair_verdict(0.856, changed=3) == "ok"


def test_a_high_scoring_pair_with_no_changed_block_is_still_a_copy():
    """Q08_0: 0.982 global, nothing anywhere in the frame moved."""
    assert end_pair_verdict(0.982, changed=0) == "copy"


def test_one_block_is_enough():
    """0 vs 3 with nothing between, so the law is 'something changed somewhere'
    rather than a count tuned to the eleven pairs that happened to be measured."""
    assert end_pair_verdict(0.95, changed=1) == "ok"


def test_the_floor_is_untouched_by_any_of_this():
    assert end_pair_verdict(0.166, changed=5) == "restaged"
    assert end_pair_verdict(0.166, changed=5, size="insert") == "ok"


def test_a_pair_inside_the_band_never_needed_the_blocks():
    assert end_pair_verdict(0.60) == "ok"
    assert end_pair_verdict(0.60, changed=0) == "ok"


def test_not_knowing_the_blocks_keeps_the_old_ceiling():
    """A caller with only the global score gets the rule that refuses more."""
    assert end_pair_verdict(0.982) == "copy"


def test_the_block_floor_is_named():
    assert 0.0 < BLOCK_FLOOR < 0.5


def test_reaches_reads_the_blocks():
    import inspect

    from studio import episode_seq_board as sq
    assert "changed_blocks" in inspect.getsource(sq.reaches)


def test_a_change_smeared_across_two_blocks_is_not_a_changed_block():
    """Half of each of two blocks reads about 0.5, over the floor.  A change has
    to BE somewhere."""
    a = cell()
    b = np.asarray(a).copy()
    b[12:24, 6:18] = np.random.RandomState(3).randint(0, 255, (12, 12), dtype=np.uint8)
    assert changed_blocks(a, Image.fromarray(b)) == 0
