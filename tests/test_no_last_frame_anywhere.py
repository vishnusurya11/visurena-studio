"""THE OWNER'S RULE, 2026-09-16: nothing in this pipeline makes a last frame.

Said three times in three days, and it has to hold on three artefacts, because
the last two times it was written down it was honoured on one of them and
bypassed on the others:

    the SHEET     draws no END panel, so no END cell exists to be pinned
    the TAKE      stages no END cell and declares no picture a last frame
    the PROMPT    is refused by the lint if it declares one anyway

Why (`docs/calibration/end_frames.md`): the model races to the last-frame
picture and holds it. A near one freezes the segment; a far one dissolves
whatever separates the two pictures, which is the warping the owner saw.
"""
import sys

import pytest

from studio import episode_ref_official as ro
from studio import episode_seq_board as sq

sys.path.insert(0, "scripts/episode")


SEGS = [
    {"shot": 0, "sub": 0, "size": "wide", "path": 0.0, "frame": "A man on the plain.",
     "motion": "The camera pushes in on the man across the whole shot, travelling two long strides.",
     "camera": "The camera stands on the slope at a standing man's eye, a 35mm lens.",
     "at_rest": "The bones lie beside the ruts.", "end_frame": "", "changed": ""},
    {"shot": 1, "sub": 0, "size": "close", "path": 0.5, "frame": "His face.",
     "motion": "The camera holds a static shot; his chin comes up a finger's breadth.",
     "camera": "The camera stands a pace from him at his own eye, a 50mm lens.",
     "at_rest": "His hat sits on his head.", "end_frame": "", "changed": ""},
]


# ---- the sheet ------------------------------------------------------------

def test_a_sheet_of_two_panels_on_a_nine_cell_grid_draws_no_END_panel():
    """Seven spare cells, and not one of them becomes an END panel.

    `with_ends` used to fill every spare cell with one, which is how the cells
    existed at all. Nothing downstream consumes them now, so drawing them is
    waste and a standing invitation to pin them again."""
    panels = sq.with_ends(SEGS, spare=7)
    assert panels[:2] == SEGS
    assert not [p for p in panels if p.get("end")]


def test_a_spare_cell_becomes_an_ALTERNATE_and_never_a_black_one():
    """A sheet with black cells is a sheet the owner sent back, and the grid table
    is coarse (3 / 6 / 9 cells), so spares are unavoidable. They used to be filled
    with END panels; they are filled with ALTERNATES now -- another angle of a
    real moment, which is the first thing an editor asks for when a take fails,
    and which no take can mistake for a destination."""
    panels = sq.with_ends(SEGS, spare=1)
    assert len(panels) == 3
    spare = panels[-1]
    assert spare["alt"] is True and spare.get("end") is not True
    assert spare["of"] in (1, 2)
    assert spare["frame"] and spare["motion"]


def test_an_alternate_cell_is_named_apart_from_its_own_panel():
    assert sq.cell_name(3, 0) == "Q03_0.png"
    assert sq.cell_name(3, 0, alt=True) == "Q03_0A.png"
    assert sq.cell_name(3, 0, end=True) == "Q03_0E.png"


def test_the_packer_fills_every_cell_of_the_grid_it_asks_for():
    """The GRID gate refuses a sheet whose prompt says nine and whose packer sent
    seven. Removing END panels broke that on every setup until spares were
    filled, and the break showed up as a paid sheet refused after the draw."""
    for count in range(1, 10):
        segs = [dict(SEGS[0], shot=k, sub=0) for k in range(count)]
        for panels, _route, (cols, rows, _canvas) in sq.sheets(segs, aspect="9:16"):
            assert len(panels) == cols * rows


def test_the_switch_is_what_turns_it_off_so_the_control_stays_runnable(monkeypatch):
    """`DRAW_ENDS` is kept, like `takes_r2v.NO_ENDS`, so the comparison can be
    reproduced -- not because anything asks for it."""
    monkeypatch.setattr(sq, "DRAW_ENDS", True)
    assert len(sq.with_ends(SEGS, spare=7)) > len(SEGS)


# ---- the take -------------------------------------------------------------

def test_a_take_is_given_no_END_cell_whatever_is_drawn_on_disk(tmp_path):
    import takes_r2v as tr
    from PIL import Image
    Image.new("RGB", (64, 64), (30, 30, 30)).save(tmp_path / "Q00_0.png")
    Image.new("RGB", (64, 64), (40, 40, 40)).save(tmp_path / "Q00_0E.png")
    assert tr.NO_ENDS is True
    assert tr.end_cells(tmp_path, [(0, 0)]) == []


# ---- the prompt -----------------------------------------------------------

@pytest.mark.parametrize("text", [
    "subject_definitions:\n<Picture 3> is the last frame of [Shot 1], action completed.",
    "retention_analysis:\n<Picture 3> ([Shot 1] last frame): fully_preserved - viewpoint.",
])
def test_the_lint_refuses_a_prompt_that_declares_a_last_frame(text):
    assert any("last frame" in fault for fault in ro.lint(text))


def test_the_lint_leaves_the_spec_s_own_continuation_clause_alone():
    text = ("detailed_description:\n[Shot 1] From 00:00 to 00:03. The shot begins from "
            "<Picture 3>: a close shot. At 00:02 he leans onto the stick, and the lean "
            "continues to the last frame of the shot.")
    assert not [f for f in ro.lint(text) if "last frame" in f]
