"""A `shadow` on a policy row is a NEWER judge version run beside the current
one on the same artefact.  It writes `<verdict>.shadow.json` for the bench and
signs nothing: the verdict file names the current judge."""
from __future__ import annotations

import json

from studio import eye_verdict as ev, judged_gate
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


def _verdict(judge, version, passed, faults=()):
    return Verdict(judge=judge, version=version, passed=passed, faults=list(faults),
                   confidence=1.0, reads=1)


def test_the_shadow_writes_a_sidecar_and_the_current_judge_signs(tmp_path):
    ctx = Ctx(tmp_path)
    board = tmp_path / "board"
    board.mkdir()
    (board / "shot_01.png").write_bytes(b"\x01" * 8)
    pics = [board / "shot_01.png"]
    policy = Policy(state="auto", judge="panel_eye@1", shadow="panel_eye@2",
                    decision="2026-09-24-automate-the-taste-gates", terminal="keep_best")
    shadow_read = _verdict("panel_eye", "2", False, [Fault(kind="hat", where="shot_01")])
    signed = judged_gate.clear(
        ctx, "EYE_PANELS", judge=lambda: _verdict("panel_eye", "1", True),
        sign=lambda v: ev.sign_verdict(board, pics, v),
        ladder=judged_gate.Rungs(Ladder([Rung("seed", 100)], "keep_best"), take=lambda *a: None),
        terminal=lambda v: v, policy=policy, shadow=lambda: shadow_read)
    doc = json.loads(signed.read_text(encoding="utf-8"))
    assert doc["verdict"] == "pass" and doc["signed_by"] == "judge:panel_eye@1"
    sidecar = signed.with_suffix(".shadow.json")
    side = json.loads(sidecar.read_text(encoding="utf-8"))
    assert side["judge"] == "panel_eye" and side["version"] == "2" and side["passed"] is False
    assert sorted(p.name for p in board.glob("eye_*")) == [signed.name, sidecar.name]
    assert ev.passed(board, pics) and ctx.learned == []
