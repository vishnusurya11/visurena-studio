"""BUILD_PLAN 6.2 R5: replay Jekyll ep01's attempts.json, ladder.json and take-eye verdict (copies under
tests/fixtures/ep01_replay/P08/) through the new ladder, $0: the rounds spent are the rounds that
rendered (the real run burned two at 0.0 s), T01's gait gets the plan's verb and T08's clones a seed,
the eight Se-only warps route to nothing, and every fault leaves the terminal with its settled mark."""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from types import SimpleNamespace

from studio import audit_rows, eye_verdict as ev, judged_gate, step_attempts, take_ladder as tl
from studio.gate_policy import Policy
from studio.judges.verdict import Fault, Verdict
from studio.run_budget import EPISODE_SHARES, Budget

FIX = Path(__file__).parent / "fixtures" / "ep01_replay" / "P08"
AUTO = Policy(state="auto", judge="take_eye@1", decision="2026-09-24-automate-the-taste-gates", terminal="keep_best")


class Ctx:
    def __init__(self, tmp_path):
        self.stage, self.unit = "episode", "ep01"
        self.book_dir = tmp_path / "book"
        self.home = self.book_dir / "episodes" / "ep01"
        self.room = self.home / "takes" / "r2v"
        self.room.mkdir(parents=True)
        self.budget = Budget(18000, EPISODE_SHARES, clock=lambda: 0.0)
        self.learned, self.said = [], []

    def learn(self, learning):
        self.learned.append(learning)

    def log(self, msg, **kw):
        self.said.append(msg)


def replay_world(tmp_path, monkeypatch):
    ctx = Ctx(tmp_path)
    attempts = json.loads((FIX / "attempts.json").read_text(encoding="utf-8"))
    attempts.pop("retakes")                                  # the two empty rounds the real run burned
    (ctx.home / "attempts.json").write_text(json.dumps(attempts), encoding="utf-8")
    shutil.copy(FIX / "ladder.json", ctx.room / "ladder.json")
    shutil.copy(FIX / "plan.json", ctx.home / "plan.json")
    (ctx.home / "storyboard").mkdir()
    (ctx.home / "storyboard" / "panel_content.json").write_text(json.dumps([{"shot": 8, "passed": True}]))
    doc = json.loads((FIX / "eye_b368ae93.json").read_text(encoding="utf-8"))
    for f in doc["faults"]:
        (ctx.room / f"{f['where']}.mp4").write_bytes(f["where"].encode())
    monkeypatch.setattr(tl.episode_home, "write_plan", lambda path, d: path.write_text(json.dumps(d), encoding="utf-8"))
    return ctx, [Fault(**f) for f in doc["faults"]]


def run_climb(ctx, faults, monkeypatch):
    sent, clock = [], iter(range(0, 100000, 600))
    monkeypatch.setattr(tl, "retake", lambda c, idx, why, flag, trims=None: sent.append(sorted(idx)))
    monkeypatch.setattr(tl, "wall", lambda: float(next(clock)))
    verdict = Verdict(judge="take_eye", version="1", passed=False, confidence=1.0, reads=1, faults=faults)
    plan = SimpleNamespace(lines=[], turn=lambda: SimpleNamespace(index=98), button=lambda: SimpleNamespace(shot=99))
    takes = sorted(ctx.room.glob("T??.mp4"))
    signed = judged_gate.clear(ctx, "EYE_TAKES", judge=lambda: verdict,
                               sign=lambda v: ev.sign_verdict(ctx.room, takes, v),
                               ladder=tl.rungs(ctx, plan, "--approved=render"),
                               terminal=tl.terminal_for(ctx, plan), policy=AUTO)
    return sent, signed


def test_the_rounds_spent_are_the_rounds_that_rendered(tmp_path, monkeypatch):
    ctx, faults = replay_world(tmp_path, monkeypatch)
    sent, _signed = run_climb(ctx, faults, monkeypatch)
    assert sent == [[1, 8]]                                   # T01 (gait) and T08 (clones); the warps wait
    assert step_attempts.count(ctx.home, "retakes") == 1      # not 2
    assert step_attempts.seconds(ctx.home, "retakes") == 600.0  # not 0.0


def test_t01_gets_the_plan_verb_and_t08_a_seed(tmp_path, monkeypatch):
    ctx, faults = replay_world(tmp_path, monkeypatch)
    routed = tl.route(Verdict(judge="take_eye", version="1", passed=False, confidence=1.0, reads=1, faults=faults),
                      ctx.room)
    assert sorted(routed["gait_verb"]) == [1] and sorted(routed["seed"]) == [8]
    assert set(routed) == {"gait_verb", "seed"}               # all eight Se-only warps route to nothing
    run_climb(ctx, faults, monkeypatch)
    motion = next(s["motion"] for s in json.loads((ctx.home / "plan.json").read_text())["shots"] if s["index"] == 1)
    assert "walking pace" not in motion and motion.startswith("The camera tracks beside the two walkers")


def test_every_fault_leaves_the_terminal_settled_and_the_warps_are_on_the_watch_list(tmp_path, monkeypatch):
    ctx, faults = replay_world(tmp_path, monkeypatch)
    _sent, signed = run_climb(ctx, faults, monkeypatch)
    doc = json.loads(signed.read_text(encoding="utf-8"))
    assert len(doc["faults"]) == 13 and all(f["evidence"]["settled"] == "keep_best" for f in doc["faults"])
    watch = [r for r in audit_rows.load(ctx.book_dir) if r.terminal == "watch"]
    assert {f["take"] for f in watch[0].faults if f["class"] == "warp_se"} == {
        "T07", "T10", "T15", "T16", "T19", "T20", "T21", "T24"}
