"""`judged_gate.clear` on an `auto` gate: the judge passes, the verdict file is
signed `judge:<name>@<version>`, no rung is taken, nothing is learned, and the
next step's `passed` is true."""
from __future__ import annotations

import json

import pytest

from studio import eye_verdict as ev, judged_gate
from studio.gate_policy import Policy
from studio.judges.verdict import Verdict
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


def _board(tmp_path):
    board = tmp_path / "board"
    board.mkdir()
    (board / "shot_01.png").write_bytes(b"\x01" * 8)
    return board, [board / "shot_01.png"]


def test_a_pass_is_signed_in_the_judge_name(tmp_path):
    ctx = Ctx(tmp_path)
    board, pics = _board(tmp_path)
    taken = []
    signed = judged_gate.clear(
        ctx, "EYE_PANELS",
        judge=lambda: Verdict(judge="panel_eye", version="1", passed=True, confidence=1.0, reads=1),
        sign=lambda v: ev.sign_verdict(board, pics, v),
        ladder=judged_gate.Rungs(Ladder([Rung("seed", 100)], "keep_best"), take=lambda *a: taken.append(a)),
        terminal=lambda v: v, policy=AUTO)
    doc = json.loads(signed.read_text(encoding="utf-8"))
    assert doc["verdict"] == "pass" and doc["signed_by"].startswith("judge:panel_eye@1")
    assert ev.passed(board, pics)
    assert taken == [] and ctx.learned == []
    assert not (ctx.book_dir / "audit" / "rows.jsonl").exists()


def test_the_real_registry_row_clears_the_same_way(tmp_path):
    """No policy injected: the row comes from gates.yaml at the repo root."""
    ctx = Ctx(tmp_path)
    board, pics = _board(tmp_path)
    signed = judged_gate.clear(
        ctx, "EYE_PANELS",
        judge=lambda: Verdict(judge="panel_eye", version="1", passed=True, confidence=1.0, reads=1),
        sign=lambda v: ev.sign_verdict(board, pics, v),
        ladder=judged_gate.Rungs(Ladder([Rung("seed", 100)], "keep_best"), take=lambda *a: None),
        terminal=lambda v: v)
    assert json.loads(signed.read_text(encoding="utf-8"))["signed_by"] == "judge:panel_eye@1"


def test_a_human_gate_is_not_cleared_by_a_judge(tmp_path):
    ctx = Ctx(tmp_path)
    board, pics = _board(tmp_path)
    with pytest.raises(SystemExit, match="human"):
        judged_gate.clear(
            ctx, "PUBLISH",
            judge=lambda: Verdict(judge="x", version="1", passed=True, confidence=1.0),
            sign=lambda v: ev.sign_verdict(board, pics, v),
            ladder=judged_gate.Rungs(Ladder([], "flag"), take=lambda *a: None),
            terminal=lambda v: v, policy=Policy(state="human"))
    assert list(board.glob("eye_*")) == []
