"""A fault takes a rung: the ladder re-renders, the judge reads again, one
learning per rung.  While the ladder climbs, no verdict file exists -- a fault
is never written for `require` to refuse on."""
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


AUTO = Policy(state="auto", judge="panel_eye@1", decision="2026-09-24-automate-the-taste-gates",
              terminal="keep_best")


def test_a_fault_climbs_one_rung_then_signs_the_pass(tmp_path):
    ctx = Ctx(tmp_path)
    board = tmp_path / "board"
    board.mkdir()
    (board / "shot_01.png").write_bytes(b"\x01" * 8)
    pics = [board / "shot_01.png"]
    reads = iter([
        Verdict(judge="panel_eye", version="1", passed=False, confidence=1.0, reads=1,
                faults=[Fault(kind="clones", where="shot_01")]),
        Verdict(judge="panel_eye", version="1", passed=True, confidence=1.0, reads=1)])
    seen = []

    def take(rung, i, verdict):
        seen.append((rung.name, i, [f.kind for f in verdict.faults], list(board.glob("eye_*"))))
        (board / "shot_01.png").write_bytes(b"\x02" * 8)          # redrawn on a new seed

    signed = judged_gate.clear(
        ctx, "EYE_PANELS", judge=lambda: next(reads),
        sign=lambda v: ev.sign_verdict(board, pics, v),
        ladder=judged_gate.Rungs(Ladder([Rung("redraw_grid_seed", 100), Rung("reprose", 100)], "keep_best"),
                                 take=take),
        terminal=lambda v: v, policy=AUTO)
    assert seen == [("redraw_grid_seed", 0, ["clones"], [])]
    doc = json.loads(signed.read_text(encoding="utf-8"))
    assert doc["verdict"] == "pass" and doc["signed_by"] == "judge:panel_eye@1"
    assert [l.action for l in ctx.learned] == ["redraw_grid_seed", "pass"]
    assert ctx.learned[0].gate == "EYE_PANELS" and ctx.learned[0].terminal is False
    assert "clones" in ctx.learned[0].note
    assert not (ctx.book_dir / "audit" / "rows.jsonl").exists()
