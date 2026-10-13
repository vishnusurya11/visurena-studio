"""A take that staged its storyboard panel is judged AGAINST that panel.

Jekyll ep01 (2026-10-13, MOTION.md cause 5): every one of 27 takes pinned
`storyboard/h3/shot_NN.png` as its first frame, and every DQ record printed
foreign, cut-landing, drift, coherence off-board and last-vs-cell as
"not measured (no cell)": the record's `anchors` are empty under --from-refs, so
the gate looked for a board, found none and judged the frames alone.  The
panel IS the board: one cell, pinned at frame 0.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from studio import cut_landing, motion_gate

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("take_dq_panel", ROOT / "scripts" / "episode" / "take_dq.py")
take_dq = importlib.util.module_from_spec(spec)
sys.modules["take_dq_panel"] = take_dq
spec.loader.exec_module(take_dq)


def staged(book: Path, rel: str) -> Path:
    p = book / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b"png")
    return p


def test_a_staged_panel_becomes_the_one_cell_at_frame_zero(tmp_path):
    panel = staged(tmp_path, "episodes/ep01/storyboard/h3/shot_13.png")
    rec = {"index": 13, "anchors": [], "refs": ["refs/characters/x/sheet_front.png",
                                                 "episodes/ep01/storyboard/h3/shot_13.png"]}
    anchors, cells = take_dq.panel_board(rec, tmp_path)
    assert anchors == [["shot_13.png", 0]] and cells == panel.parent


def test_a_pinned_cell_take_keeps_its_own_board(tmp_path):
    staged(tmp_path, "episodes/ep01/storyboard/h3/shot_13.png")
    rec = {"anchors": [["Q13_0.png", 0]], "refs": ["episodes/ep01/storyboard/h3/shot_13.png"]}
    assert take_dq.panel_board(rec, tmp_path) is None


def test_no_panel_staged_is_still_cellless(tmp_path):
    assert take_dq.panel_board({"anchors": [], "refs": ["refs/locations/a/wide.png"]}, tmp_path) is None


def test_a_panel_named_but_absent_is_not_a_board(tmp_path):
    rec = {"anchors": [], "refs": ["episodes/ep01/storyboard/h3/shot_02.png"]}
    assert take_dq.panel_board(rec, tmp_path) is None


def test_a_panel_cell_names_its_shot():
    assert motion_gate.shot_of("shot_13.png") == 13
    assert motion_gate.shot_of("Q17_2.png") == 17


def test_the_other_panels_are_foreign_pictures(tmp_path):
    for n in (1, 2, 3):
        staged(tmp_path, f"h3/shot_{n:02d}.png")
    assert cut_landing.foreign_names(tmp_path / "h3", tmp_path / "plates", {"shot_02.png"}) == \
        ["shot_01.png", "shot_03.png"]


# ---- what binds on a panel board: calibrated on WotW ep19 (20 shipped takes) + Jekyll ep01 (27) ----

def gate(name, ok=False, hard=True, penalty=25.0):
    from studio.take_verdict import Gate
    return Gate(name, 1, ok, hard, "x", penalty)


def test_opening_and_offboard_are_advisory_on_a_panel_board():
    """As HARD rows they failed 8 and 11 of WotW ep19's 20 shipped takes: H3 does
    not open on, or stay on, a first-frame panel the way it held a pinned cell."""
    from studio import take_verdict as tv
    out = tv.panel_board_rows([gate("cut-landing"), gate("coherence off-board"), gate("foreign"),
                               gate("last-vs-cell")])
    hard = {g.name: g.hard for g in out}
    assert hard == {"cut-landing": False, "coherence off-board": False, "foreign": True, "last-vs-cell": True}
    assert all(g.penalty == 25.0 for g in out)            # still scored: best-of-N prefers the faithful take
    assert "panel" in out[0].note


def test_a_cell_board_keeps_every_row_hard():
    from studio import take_verdict as tv
    rows = [gate("cut-landing"), gate("coherence off-board")]
    assert [g.hard for g in tv.board_rows(rows, {"board": "cells"})] == [True, True]
    assert [g.hard for g in tv.board_rows(rows, {"board": "panel"})] == [False, False]
