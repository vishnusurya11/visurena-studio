"""A fix that reaches one call site and not the other has not been made.

`end_pair_verdict` grew two rules: the FLOOR is dropped for a size whose subject
fills the frame (an insert -- a coin turning over scored 0.166 and was called
"re-staged"), and the CEILING is overturned by one block of real change (a
locked-off camera where the change sits in the doorway scored 0.856 and was
called a "copy").

Both reached `reaches()`, which decides whether a TAKE may aim at an END cell.
NEITHER reached `duplicates()` -- the call site that judges a DRAWN SHEET, and
the only one that both SPENDS MONEY (a STRICT redraw) and DESTROYS WORK
(`drop_end_copies` retires the cell).

MEASURED on episode 4's own sheet report, `seq_rance_parlour.dq.json`: eight END
pairs refused as duplicates, costing two STRICT redraws. Cross-referenced
against the table in END_CEILING's own docstring, FIVE of the eight are not
copies under the rule this repo already believes -- Q09 (0.807, 3 changed
blocks), Q15 (0.938, 4), Q20 (0.856, 3), Q21 (0.856, 3), and Q10, the
half-sovereign insert at 0.166 that the insert exemption exists for.

`take_verdict.frames_for` had the same gap on its disk-fallback path.
"""
import numpy as np
import pytest
from PIL import Image

from studio import episode_seq_board as sq


def seg(shot: int, sub: int = 0, end: bool = False) -> dict:
    return {"shot": shot, "sub": sub, "end": end, "size": "medium"}


def noise(tmp_path, name: str, seed: int) -> "Path":
    """`duplicates` takes PATHS and loads them itself."""
    out = tmp_path / name
    Image.fromarray(np.random.RandomState(seed).randint(0, 255, (84, 48), dtype=np.uint8)).save(out)
    return out


def one_block_changed(tmp_path, name: str, base) -> "Path":
    a = np.asarray(Image.open(base).convert("L")).copy()
    a[12:24, 12:24] = np.random.RandomState(99).randint(0, 255, (12, 12), dtype=np.uint8)
    out = tmp_path / name
    Image.fromarray(a).save(out)
    return out


def test_an_end_pair_with_a_changed_block_is_not_a_duplicate(tmp_path):
    """Q21: 0.856 global, the two men walk out of the doorway."""
    start = noise(tmp_path, "a.png", 1)
    segs = [seg(21), seg(21, end=True)]
    assert sq.duplicates([start, one_block_changed(tmp_path, "b.png", start)], segs) == []


def test_an_end_pair_with_nothing_changed_is_still_a_duplicate(tmp_path):
    """Q08: 0.982 global, nothing anywhere in the frame moved."""
    start = noise(tmp_path, "a.png", 1)
    segs = [seg(8), seg(8, end=True)]
    assert sq.duplicates([start, start], segs) != []


def test_an_insert_end_pair_is_not_refused_for_being_different(tmp_path):
    """Q10: the half-sovereign turns over, 0.166 -- the insert exemption."""
    segs = [dict(seg(10), size="insert"), dict(seg(10, end=True), size="insert")]
    assert sq.duplicates([noise(tmp_path, "a.png", 1), noise(tmp_path, "b.png", 2)], segs) == []


def test_a_non_insert_end_pair_that_re_stages_is_still_refused(tmp_path):
    segs = [seg(10), seg(10, end=True)]
    assert sq.duplicates([noise(tmp_path, "a.png", 1), noise(tmp_path, "b.png", 2)], segs) != []


def test_two_ordinary_panels_that_are_one_picture_are_still_refused(tmp_path):
    start = noise(tmp_path, "a.png", 1)
    assert sq.duplicates([start, start], [seg(22), seg(24)]) != []


def test_the_verdict_is_given_both_rules_at_this_site():
    import inspect
    src = inspect.getsource(sq.duplicates)
    assert "changed_blocks" in src and "size" in src


def test_the_dq_disk_fallback_asks_with_the_size_too():
    import inspect
    from studio import take_verdict as tv
    src = inspect.getsource(tv)
    assert "sq.reaches(cells / n, cells / end_name)" not in src, "reaches called without a size"
