"""Rungs spent: the terminal rung keeps what it keeps and never asks.  It signs
the verdict `flagged` with the faults listed, writes a terminal learning, and
appends one row to `library/<book>/audit/rows.jsonl` for the owner's look."""
from __future__ import annotations

import json

from studio import audit_rows, eye_verdict as ev, judged_gate
from studio.gate_policy import Policy
from studio.judges.verdict import Fault, Verdict
from studio.ladder import Ladder, Rung
from studio.run_budget import EPISODE_SHARES, Budget


class Ctx:
    def __init__(self, tmp_path):
        self.stage, self.unit = "episode", "ep01"
        self.book_dir = tmp_path / "book"
        self.budget = Budget(18000, EPISODE_SHARES, clock=lambda: 0.0)
        self.learned = []

    def learn(self, learning):
        self.learned.append(learning)


AUTO = Policy(state="auto", judge="panel_eye@1", decision="2026-09-24-automate-the-taste-gates",
              terminal="keep_best")


def failing():
    return Verdict(judge="panel_eye", version="1", passed=False, confidence=1.0, reads=1,
                   faults=[Fault(kind="clones", where="shot_01", evidence={"cosine": 0.8})])


def test_the_terminal_signs_flagged_learns_and_writes_the_audit_row(tmp_path):
    ctx = Ctx(tmp_path)
    board = tmp_path / "book" / "episodes" / "ep01" / "storyboard"
    board.mkdir(parents=True)
    (board / "shot_01.png").write_bytes(b"\x01" * 8)
    pics = [board / "shot_01.png"]
    kept = []
    signed = judged_gate.clear(
        ctx, "EYE_PANELS", judge=failing,
        sign=lambda v: ev.sign_verdict(board, pics, v),
        ladder=judged_gate.Rungs(Ladder([Rung("redraw_grid_seed", 100), Rung("reprose", 100)], "keep_best"),
                                 take=lambda rung, i, v: None),
        terminal=lambda v: kept.append(v.terminal) or v, policy=AUTO)
    doc = json.loads(signed.read_text(encoding="utf-8"))
    assert doc["verdict"] == "flagged" and doc["terminal"] == "keep_best"
    assert doc["signed_by"] == "judge:panel_eye@1" and doc["faults"][0]["kind"] == "clones"
    assert kept == ["keep_best"] and ev.passed(board, pics)
    actions = [(l.action, l.terminal) for l in ctx.learned]
    assert actions == [("redraw_grid_seed", False), ("reprose", False), ("keep_best", True)]
    rows = audit_rows.load(ctx.book_dir)
    assert len(rows) == 1
    row = rows[0]
    assert row.unit == "ep01" and row.gate == "EYE_PANELS" and row.judge == "judge:panel_eye@1"
    assert row.terminal == "keep_best" and row.faults[0]["kind"] == "clones"
    assert row.sha8 == doc["sha8"] and row.artefact == "episodes/ep01/storyboard/" + signed.name
    assert row.ts
