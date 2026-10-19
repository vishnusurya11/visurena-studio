"""K11: `Rungs.take` returns RungResult(changed, reason, seconds).  A round is spent only when a
take's bytes changed (a render, a trim, a head cut) or a render was queued; a take that returned
without doing anything ends the climb and says why.  Jekyll ep01 (2026-10-18): two batched rounds
spent at 0.0 s each, then a 13-fault verdict re-read twice unchanged.  `None` keeps its old meaning
for the plan and panel ladders."""
from __future__ import annotations

import json
import types

from studio import eye_verdict as ev, judged_gate, step_attempts, take_ladder as tl
from studio.gate_policy import Policy
from studio.judges.verdict import Fault, Verdict
from studio.ladder import Ladder, Rung
from studio.run_budget import EPISODE_SHARES, Budget

AUTO = Policy(state="auto", judge="take_eye@1", decision="2026-09-24-automate-the-taste-gates",
              terminal="keep_best")


class Ctx:
    def __init__(self, tmp_path):
        self.stage, self.unit = "episode", "ep01"
        self.book_dir = tmp_path / "book"
        self.home = self.book_dir / "episodes" / "ep01"
        (self.home / "takes" / "r2v").mkdir(parents=True, exist_ok=True)
        self.budget = Budget(18000, EPISODE_SHARES, clock=lambda: 0.0)
        self.learned, self.said = [], []

    def learn(self, learning):
        self.learned.append(learning)

    def log(self, msg, **kw):
        self.said.append(msg)


def failing():
    return Verdict(judge="take_eye", version="1", passed=False, confidence=1.0, reads=3,
                   faults=[Fault(kind="warp", where="T07")])


def climb(ctx, result, tries=2):
    room = ctx.home / "takes" / "r2v"
    (room / "T07.mp4").write_bytes(b"take")
    calls = []

    def take(rung, i, verdict):
        calls.append(i)
        return result
    judged_gate.clear(ctx, "EYE_TAKES", judge=failing,
                      sign=lambda v: ev.sign_verdict(room, [room / "T07.mp4"], v),
                      ladder=judged_gate.Rungs(Ladder([Rung("seed", 1.0, tries=tries)], "keep_best"), take=take),
                      terminal=lambda v: v, policy=AUTO)
    return calls


def test_a_take_that_changed_nothing_spends_no_round_and_ends_the_climb(tmp_path, capsys):
    ctx = Ctx(tmp_path)
    calls = climb(ctx, judged_gate.RungResult(False, "no renders", 0.0))
    assert calls == [0]                                           # not asked a second time
    assert step_attempts.count(ctx.home, "retakes") == 0
    assert "no renders" in capsys.readouterr().out


def test_a_round_that_changed_bytes_spends_one_with_its_own_seconds(tmp_path):
    ctx = Ctx(tmp_path)
    calls = climb(ctx, judged_gate.RungResult(True, "rendered 2", 42.0), tries=1)
    assert calls == [0]
    assert step_attempts.count(ctx.home, "retakes") == 1
    assert step_attempts.seconds(ctx.home, "retakes") == 42.0


def test_none_still_spends_a_round(tmp_path):
    ctx = Ctx(tmp_path)
    climb(ctx, None)
    assert step_attempts.count(ctx.home, "retakes") == 2         # the legacy ladders' meaning


def test_a_trim_only_round_still_spends(tmp_path):
    ctx = Ctx(tmp_path)
    climb(ctx, judged_gate.RungResult(True, "trimmed 1", 0.0), tries=1)
    assert step_attempts.count(ctx.home, "retakes") == 1


# ---- take_ladder.rungs().take -----------------------------------------------------------

class Money:
    """A budget with `left` seconds and no pool."""
    step = "09"

    def __init__(self, left):
        self.left = left

    def can_afford(self, step, price):
        return price <= self.left

    def pool_left(self):
        return 0.0

    def headroom(self):
        return self.left


def shot_ctx(tmp_path, monkeypatch, left):
    ctx = Ctx(tmp_path)
    ctx.budget = Money(left)
    shots = [{"index": i, "motion": "The camera tracks beside the man.", "at_rest": "a man"} for i in range(13)]
    (ctx.home / "plan.json").write_text(json.dumps({"shots": shots, "lines": []}), encoding="utf-8")
    monkeypatch.setattr(tl.episode_home, "write_plan", lambda path, doc: path.write_text(json.dumps(doc)))
    sent = []
    monkeypatch.setattr(tl, "retake", lambda ctx_, idx, why, flag, trims=None: sent.append(list(idx)))
    return ctx, sent


def thirteen():
    faults = [Fault(kind="frozen-whole", where=f"T{i:02d}") for i in range(13)]
    faults += [Fault(kind="held", where="T05"), Fault(kind="held", where="T09")]    # the worst two
    return Verdict(judge="take_eye", version="1", passed=False, confidence=1.0, reads=1, faults=faults)


def test_a_thirteen_fault_batch_keeps_the_takes_the_budget_affords_worst_first(tmp_path, monkeypatch):
    ctx, sent = shot_ctx(tmp_path, monkeypatch, left=900.0)      # 300 cold + 265 x 2 = 830 fits, x3 = 1095 does not
    rungs = tl.rungs(ctx, None, "--approved=render")
    got = rungs.take(tl.BATCH, 0, thirteen())
    assert sent == [[5, 9]]
    assert got.changed and "2 of 13" in got.reason


def test_an_unaffordable_batch_of_nothing_says_the_price_and_the_budget(tmp_path, monkeypatch):
    ctx, sent = shot_ctx(tmp_path, monkeypatch, left=100.0)
    got = tl.rungs(ctx, None, "--approved=render").take(tl.BATCH, 0, thirteen())
    assert sent == [] and not got.changed
    assert "unaffordable" in got.reason and "565" in got.reason and "100" in got.reason


def test_an_empty_route_is_not_a_round_and_says_not_routed(tmp_path, monkeypatch):
    ctx, sent = shot_ctx(tmp_path, monkeypatch, left=9000.0)
    v = Verdict(judge="take_eye", version="1", passed=False, confidence=1.0, reads=1,
                faults=[Fault(kind="look", where="T03")])
    got = tl.rungs(ctx, None, "--approved=render").take(tl.BATCH, 0, v)
    assert sent == [] and not got.changed and got.reason == "not routed"
