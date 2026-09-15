r"""A drawn sheet is reused only while the words that drew it are unchanged.

`storyboard.draw` cached on the output PATH:

    if out.exists():
        return out

so `seq_boards --setup=landing_arrest` returned in seconds and
`seq_landing_arrest_0.png` kept its 06:45 timestamp, and every cell cut from it
came back byte-identical. The prompt had changed; the filename had not.

This is why the END-panel fix appeared to do nothing twice. The first time the
fix really was a no-op (`end_panel` blanks `motion`). The second time the fix was
correct and the drawer never saw it -- and the two failures look exactly alike
from outside, because both end in a cell whose md5 has not moved.

A path is not a cache key. It names WHERE the answer was put, never WHAT was
asked. `draw` already writes the question next to the answer, in
`<sheet>.prompt.txt`, for exactly this kind of forensics; the cache now reads
the file it was already writing.

A sheet drawn before that file existed is kept, not redrawn -- the alternative
is re-spending on every sheet of six published episodes to learn nothing.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import importlib.util

spec = importlib.util.spec_from_file_location("ep_storyboard", ROOT / "scripts/episode/storyboard.py")
storyboard = importlib.util.module_from_spec(spec)
sys.modules["ep_storyboard"] = storyboard
spec.loader.exec_module(storyboard)

PROMPT = "Panel 1 - a full of the mews lane. Panel 2 - PANEL 1 ONE ACTION LATER, from the same camera."
MOVED = "Panel 1 - a full of the mews lane. Panel 2 - PANEL 1 ONE ACTION LATER, from two long strides NEARER."


@pytest.fixture
def sheet(tmp_path):
    out = tmp_path / "seq_mews_lane_0.png"
    out.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 64)
    return out


def refs(tmp_path, *names):
    made = []
    for n in names:
        p = tmp_path / n
        p.write_bytes(b"ref")
        made.append(p)
    return made


def test_the_same_words_reuse_the_sheet(sheet, tmp_path):
    images = refs(tmp_path, "plate_mews_lane.png", "char-holmes.png")
    storyboard.remember(sheet, PROMPT, images)
    assert storyboard.cached(sheet, PROMPT, images)


def test_changed_words_do_not(sheet, tmp_path):
    """The case that cost two rounds: the prompt moved and the filename did not."""
    images = refs(tmp_path, "plate_mews_lane.png")
    storyboard.remember(sheet, PROMPT, images)
    assert not storyboard.cached(sheet, MOVED, images)


def test_a_changed_reference_list_does_not_either(sheet, tmp_path):
    """The references are half the instruction: the same words over a different
    wardrobe card draw a different picture."""
    first = refs(tmp_path, "plate_mews_lane.png", "char-holmes-indoor.png")
    storyboard.remember(sheet, PROMPT, first)
    second = refs(tmp_path, "plate_mews_lane.png", "char-holmes-outdoor.png")
    assert not storyboard.cached(sheet, PROMPT, second)


def test_the_order_of_the_references_is_part_of_the_question(sheet, tmp_path):
    """`shift_indices` numbers the panels against this order; swapping two is
    the fault that drew a walking stick as an iron poker."""
    a, b = refs(tmp_path, "plate.png", "char.png")
    storyboard.remember(sheet, PROMPT, [a, b])
    assert not storyboard.cached(sheet, PROMPT, [b, a])


def test_a_sheet_that_was_never_drawn_is_not_cached(tmp_path):
    assert not storyboard.cached(tmp_path / "nothing.png", PROMPT, [])


def test_a_sheet_from_before_the_record_is_kept(sheet, tmp_path):
    """Six published episodes have sheets with no prompt file beside them.
    Re-spending on all of them to learn nothing is not a cache miss worth having."""
    assert storyboard.cached(sheet, PROMPT, refs(tmp_path, "plate.png"))


def test_the_record_is_the_file_draw_already_wrote(sheet, tmp_path):
    """Not a new sidecar: `draw` has always written <sheet>.prompt.txt."""
    images = refs(tmp_path, "plate.png")
    storyboard.remember(sheet, PROMPT, images)
    assert sheet.with_suffix(".prompt.txt").exists()
    assert PROMPT in sheet.with_suffix(".prompt.txt").read_text(encoding="utf-8")
    assert "plate.png" in sheet.with_suffix(".prompt.txt").read_text(encoding="utf-8")
