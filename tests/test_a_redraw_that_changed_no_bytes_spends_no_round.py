"""P05 item 4 / B1: a redraw round is spent only when a panel's bytes changed.  A rung whose rebuild
left every panel as it was (a grid skipped at the cap, a wall stop, a render that returned the same
picture) is refunded, so the episode's two regrid rounds are not burned on nothing."""
from __future__ import annotations

import json

from studio import eye_verdict, judged_gate, panel_ladder, step_attempts
from studio.judges.verdict import Fault, Verdict
from test_a_panel_fault_climbs_seed_then_reprose_then_flags import AUTO, PLAN, Ctx, board_of, machine_verdicts


def clones():
    return Verdict(judge="panel_eye", version="1", passed=False, confidence=1.0, reads=25,
                   faults=[Fault(kind="clones", where="shot_11", evidence={"cosine": 0.8})])


def run(tmp_path, rebuild):
    ctx = Ctx(tmp_path)
    board, _ = board_of(ctx)
    shots = [s["index"] for s in json.loads(PLAN.read_text(encoding="utf-8"))["shots"]]
    machine_verdicts(board, shots, failing=11)
    climb = panel_ladder.climb(ctx, lambda only=None: rebuild(board), cap=AUTO.max_grids)
    judged_gate.clear(
        ctx, "EYE_PANELS", judge=clones,
        sign=lambda v: eye_verdict.sign_verdict(board, sorted(board.glob("shot_*.png")), v),
        ladder=climb.rungs, terminal=climb.keep_best, policy=AUTO)
    return ctx


def test_rounds_that_changed_no_bytes_are_refunded(tmp_path):
    ctx = run(tmp_path, lambda board: None)
    assert step_attempts.count(ctx.home, panel_ladder.REGRID) == 0


def test_a_round_that_rewrote_a_panel_is_spent(tmp_path):
    turns = iter(range(1, 10))
    ctx = run(tmp_path, lambda board: (board / "shot_11.png").write_bytes(bytes([next(turns) + 100]) * 8))
    assert step_attempts.count(ctx.home, panel_ladder.REGRID) == 2


def test_the_digest_follows_the_panel_bytes(tmp_path):
    (tmp_path / "shot_01.png").write_bytes(b"a")
    first = panel_ladder.panel_digest(tmp_path)
    assert first == panel_ladder.panel_digest(tmp_path)
    (tmp_path / "shot_01.png").write_bytes(b"b")
    assert panel_ladder.panel_digest(tmp_path) != first
