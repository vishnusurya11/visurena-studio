"""The INPUTS page: what every picture and prompt going in actually is.

`runcards.py` answers "what came out and what went wrong", and it can only show
a take's staged references after the render, because it reads them from the
post-render record. This page answers "what goes in", reads `prompts.json`, and
therefore works BEFORE the GPU is committed -- which is when the owner wants to
check the inputs.
"""
import importlib.util
import sys
from pathlib import Path

spec = importlib.util.spec_from_file_location("refcard", "scripts/episode/refcard.py")
rc = importlib.util.module_from_spec(spec)
sys.modules["refcard"] = rc
spec.loader.exec_module(rc)


def test_the_strict_redraw_is_the_sheet_that_was_used(tmp_path):
    """A sheet drawn twice keeps both files; the cells were cut from the LAST one."""
    (tmp_path / "seq_hall_0.png").write_bytes(b"")
    (tmp_path / "seq_hall_0_strict.png").write_bytes(b"")
    assert rc.sheet_used(tmp_path, "hall", 0).name == "seq_hall_0_strict.png"


def test_a_sheet_drawn_once_is_itself(tmp_path):
    (tmp_path / "seq_cab_0.png").write_bytes(b"")
    assert rc.sheet_used(tmp_path, "cab", 0).name == "seq_cab_0.png"


def test_a_missing_sheet_is_none(tmp_path):
    assert rc.sheet_used(tmp_path, "nowhere", 0) is None


def test_a_reference_is_numbered_in_staging_order():
    """`<Picture N>` in the prompt IS the position in `refs` (spec 1.1)."""
    refs = ["char-sherlock_holmes_indoor.png", "Q00_0.png", "Q00_1.png"]
    assert rc.numbered(refs) == [(1, "char-sherlock_holmes_indoor.png"),
                                 (2, "Q00_0.png"), (3, "Q00_1.png")]


def test_a_cast_sheet_resolves_to_the_book_and_a_cell_to_the_episode():
    assert rc.href("char-john_watson.png") == "../../refs/characters/char-john_watson.png"
    assert rc.href("Q00_0.png") == "frames/Q00_0.png"
    assert rc.href("plate_hall.png") == "frames/plate_hall.png"


def test_an_anchor_carries_its_frame_and_its_second():
    assert rc.anchor_rows([["Q00_0.png", 0], ["Q00_1.png", 68]], 24) == [
        ("Q00_0.png", 0, 0.0), ("Q00_1.png", 68, 2.833)]


def test_html_is_escaped_so_a_prompt_cannot_break_the_page():
    assert rc.esc("<Picture 1> & <Subject 2>") == "&lt;Picture 1&gt; &amp; &lt;Subject 2&gt;"
