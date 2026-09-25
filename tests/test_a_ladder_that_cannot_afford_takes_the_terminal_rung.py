"""A rung the budget cannot afford is not taken: the climb ends at the terminal
rung with a `budget` learning, no re-render, and the flagged signature."""
from __future__ import annotations

import json

from studio import eye_verdict as ev, judged_gate
from studio.gate_policy import Policy
from studio.judges.verdict import Fault, Verdict
from studio.ladder import Ladder, Rung
from studio.run_budget import EPISODE_SHARES, Budget


class Ctx:
    def __init__(self, tmp_path, clock):
        self.stage, self.unit = "episode", "ep01"
        self.book_dir = tmp_path / "book"
        self.budget = Budget(18000, EPISODE_SHARES, clock=clock)
        self.learned = []

    def learn(self, learning):
        self.learned.append(learning)


AUTO = Policy(state="auto", judge="take_eye@1", decision="2026-09-24-automate-the-taste-gates",
              terminal="keep_best")


def failing():
    return Verdict(judge="take_eye", version="1", passed=False, confidence=1.0, reads=3,
                   faults=[Fault(kind="lag", where="T07")])


def test_out_of_time_means_the_terminal_and_no_render(tmp_path):
    now = [17_900.0]                                    # 100 s left under the 18 000 s ceiling
    ctx = Ctx(tmp_path, clock=lambda: now[0])
    ctx.budget.t0 = 0.0
    room = tmp_path / "book" / "episodes" / "ep01" / "takes" / "r2v"
    room.mkdir(parents=True)
    (room / "T07.mp4").write_bytes(b"take")
    rendered = []
    signed = judged_gate.clear(
        ctx, "EYE_TAKES", judge=failing,
        sign=lambda v: ev.sign_verdict(room, [room / "T07.mp4"], v),
        ladder=judged_gate.Rungs(Ladder([Rung("seed", 300), Rung("shorter_take", 300)], "keep_best"),
                                 take=lambda rung, i, v: rendered.append(rung.name)),
        terminal=lambda v: v, policy=AUTO)
    assert rendered == []
    doc = json.loads(signed.read_text(encoding="utf-8"))
    assert doc["verdict"] == "flagged" and doc["terminal"] == "keep_best"
    gates = [(l.gate, l.action, l.terminal) for l in ctx.learned]
    assert gates == [("budget", "keep_best", True), ("EYE_TAKES", "keep_best", True)]
    assert ctx.learned[0].threshold == 300
