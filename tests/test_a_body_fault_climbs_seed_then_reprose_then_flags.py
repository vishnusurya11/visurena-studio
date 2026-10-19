"""P05 item 4: `body` and `orphan_limb` are panel fault kinds a redraw CAN cure, so a body fault
climbs seed -> reprose -> a flagged terminal (no HOLD state).  They stay out of panel_eye.CALIBRATED
until P06's E1 eval passes (recall >= 0.6, precision >= 0.8): advisory rows change no verdict."""
from __future__ import annotations

import json

from studio import eye_verdict, judged_gate, panel_ladder
from studio.judges import panel_eye
from studio.judges.verdict import Fault, Verdict
from test_a_panel_fault_climbs_seed_then_reprose_then_flags import AUTO, PLAN, Ctx, board_of, machine_verdicts


def body(kind="body", where="shot_11"):
    return Verdict(judge="panel_eye", version="1", passed=False, confidence=1.0, reads=25,
                   faults=[Fault(kind=kind, where=where, evidence={"calibrated": False})])


def test_the_body_kinds_are_not_calibrated_yet():
    assert not {"body", "orphan_limb"} & panel_eye.CALIBRATED


def test_the_body_kinds_are_redraw_curable():
    assert not {"body", "orphan_limb"} & panel_ladder.REDRAW_CANNOT_CURE
    assert panel_ladder.curable(body()) and panel_ladder.curable(body("orphan_limb"))


def test_each_body_kind_has_its_own_cure_phrase():
    assert "body" in panel_ladder.cure("body", {}).lower() or "whole" in panel_ladder.cure("body", {}).lower()
    assert panel_ladder.cure("orphan_limb", {}) != panel_ladder.cure("unread", {})
    assert panel_ladder.cure("body", {}) != panel_ladder.cure("unread", {})


def test_a_body_fault_climbs_seed_then_reprose_then_flags(tmp_path):
    ctx = Ctx(tmp_path)
    board, _ = board_of(ctx)
    shots = [s["index"] for s in json.loads(PLAN.read_text(encoding="utf-8"))["shots"]]
    machine_verdicts(board, shots, failing=11)
    signed = judged_gate.clear(
        ctx, "EYE_PANELS", judge=lambda: body(),
        sign=lambda v: eye_verdict.sign_verdict(board, sorted(board.glob("shot_*.png")), v),
        ladder=panel_ladder.rungs(ctx, lambda only=None: None, cap=AUTO.max_grids),
        terminal=panel_ladder.keep_best, policy=AUTO)
    doc = json.loads(signed.read_text(encoding="utf-8"))
    assert doc["verdict"] == "flagged" and doc["terminal"] == "keep_best"
    assert [(l.action, l.terminal) for l in ctx.learned if l.gate != "budget"] == [
        ("redraw_grid_seed", False), ("reprose", False), ("keep_best", True)]
    plan = json.loads((ctx.home / "plan.json").read_text(encoding="utf-8"))
    assert next(s["frame"] for s in plan["shots"] if s["index"] == 11).startswith(panel_ladder.cure("body", {}))
