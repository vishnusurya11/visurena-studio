"""A panel fault a redraw cannot cure takes no rung: it goes to keep_best, flagged.

MEASURED on ep13 (2026-09-27, speed plan #4): across nine EYE_PANELS climbs no
rung lowered the fault count (23->24, 20->20, 17->17, 16->16, 4->4) -- the
faults left were framing and posture, which a new seed or a reprose never
moved; they fell only to a prompt fix (9cb4609) and judge fixes.  Each rung
cost ~32 min.  The fault is still flagged: keep_best signs it, the audit row
is written, and the publish lock stops on it until the director looks.
"""
from __future__ import annotations

from test_a_panel_fault_climbs_seed_then_reprose_then_flags import AUTO, Ctx, board_of

from studio import eye_verdict, grid_layout, judged_gate, panel_ladder
from studio.judges.verdict import Fault, Verdict


def verdict(*faults: tuple[str, str]) -> Verdict:
    return Verdict(judge="panel_eye", version="1", passed=False, confidence=1.0, reads=25,
                   faults=[Fault(kind=k, where=w) for k, w in faults])


def clear(ctx, board, reads):
    return judged_gate.clear(
        ctx, "EYE_PANELS", judge=lambda: next(reads),
        sign=lambda v: eye_verdict.sign_verdict(board, sorted(board.glob("shot_*.png")), v),
        ladder=panel_ladder.rungs(ctx, lambda: None, cap=AUTO.max_grids),
        terminal=panel_ladder.keep_best, policy=AUTO)


def test_framing_and_posture_alone_take_no_rung(tmp_path):
    ctx = Ctx(tmp_path)
    board, _ = board_of(ctx)
    clear(ctx, board, iter([verdict(("framing", "shot_03"), ("posture", "shot_10"))]))
    assert ctx.launched == []
    assert [(l.action, l.terminal) for l in ctx.learned] == [("keep_best", True)]


def test_a_curable_fault_still_climbs_and_only_its_grid_is_redrawn(tmp_path):
    ctx = Ctx(tmp_path)
    board, rows = board_of(ctx)
    bad = verdict(("clones", "shot_09"), ("framing", "shot_03"))
    clear(ctx, board, iter([bad, bad, bad]))
    grid = next(r for r in rows if 9 in r["shots"])
    assert all(call[1:1 + len(grid_layout.argv(grid))] == grid_layout.argv(grid) for call in ctx.launched)
    assert [l.action for l in ctx.learned] == ["redraw_grid_seed", "reprose", "keep_best"]


def test_what_a_redraw_can_cure():
    assert panel_ladder.curable(verdict(("blur", "shot_01")))
    assert not panel_ladder.curable(verdict(("framing", "shot_01"), ("posture", "shot_02")))
