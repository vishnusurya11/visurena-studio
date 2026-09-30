"""A moving take that froze goes STRAIGHT to its cause's cure: the move type,
swapped for the catalog's substitute through write_plan, rendered in the one
batched round with its reason on the argv.  The old ladder spent a seed round
first -- measured ~0% solo across ep12-14 (five-expert debate 2026-09-30) --
so the seed rung is gone; the rung's learning still carries the seconds the
round really cost (the clock fixture)."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from studio import episode_home, eye_verdict as ev, judged_gate, take_ladder
from studio.gate_policy import Policy
from studio.judges.verdict import Fault, Verdict
from studio.run_budget import EPISODE_SHARES, Budget

ROOT = Path(__file__).resolve().parents[1]
CLOCK = ROOT / "tests" / "fixtures" / "clock" / "timing_ep.jsonl"
PLAN = ROOT / "tests" / "fixtures" / "episodes" / "ep05_plan.json"
AUTO = Policy(state="auto", judge="take_eye@1", decision="2026-09-24-automate-the-taste-gates",
              terminal="keep_best", still_max=2)


def timing() -> dict[str, float]:
    """Seconds per clock stage, the retake round's rows of the fixture."""
    rows = [json.loads(l) for l in CLOCK.read_text(encoding="utf-8").splitlines() if l.strip()]
    return {r["stage"]: r["seconds"] for r in rows if "retake" in r["note"] or r["note"] == "7 9"}


class Ctx:
    def __init__(self, tmp_path):
        self.stage, self.unit, self.number, self.book_id = "episode", "ep05", 5, "book"
        self.book_dir = tmp_path / "book"
        self.home = self.book_dir / "episodes" / "ep05"
        self.now = [0.0]
        self.budget = Budget(18000, EPISODE_SHARES, clock=lambda: self.now[0])
        self.learned, self.launched, self.cost = [], [], timing()

    def learn(self, learning):
        self.learned.append(learning)

    def run_script(self, script, *extra, gpu=False, clock=None):
        self.launched.append([script, *extra])
        self.now[0] += self.cost.get(clock, 0.0)
        return 0


def frozen(repeated: bool) -> Verdict:
    return Verdict(judge="take_eye", version="1", passed=False, confidence=1.0, reads=1,
                   faults=[Fault(kind="frozen-at-start", where="T07",
                                 evidence={"value": 1.4, "repeated": repeated})])


def test_the_freeze_on_a_moving_take_wants_a_seed_and_repeated_wants_the_move():
    moving = "The camera tracks beside the walker as he strides; his stick swings"
    assert take_ladder.wants(frozen(False).faults[0], "seed", moving)
    assert not take_ladder.wants(frozen(True).faults[0], "seed", moving)
    assert take_ladder.wants(frozen(True).faults[0], "move_type", moving)
    locked = "The camera holds a locked-off frame; he writes"
    assert not take_ladder.wants(frozen(False).faults[0], "seed", locked)   # a still take that froze
    assert take_ladder.wants(frozen(False).faults[0], "move_type", locked)


def test_the_move_type_cure_renders_in_the_first_round_through_write_plan(tmp_path):
    ctx = Ctx(tmp_path)
    room = ctx.home / "takes" / "r2v"
    room.mkdir(parents=True)
    shutil.copy(PLAN, ctx.home / "plan.json")
    episode_home.write_json(room / "shots.json", [{"index": 7, "shots": [7], "measured_seconds": 6.0,
                                                   "rel_path": "episodes/ep05/takes/r2v/T07.mp4"}])
    (room / "T07.mp4").write_bytes(b"take")
    before = episode_home.load_plan(ctx.book_dir, 5).shot(7).motion
    reads = iter([frozen(False),
                  Verdict(judge="take_eye", version="1", passed=True, confidence=1.0, reads=1)])
    rungs = take_ladder.rungs(ctx, episode_home.load_plan(ctx.book_dir, 5), "--approved=render")
    signed = judged_gate.clear(ctx, "EYE_TAKES", judge=lambda: next(reads),
                               sign=lambda v: ev.sign_verdict(room, [room / "T07.mp4"], v),
                               ladder=rungs, terminal=lambda v: v, policy=AUTO)
    assert json.loads(signed.read_text(encoding="utf-8"))["verdict"] == "pass"
    assert ctx.launched[0] == ["scripts/episode/takes_r2v.py", "--from-refs", "--no-ends", "--approved=render",
                               "--retake=7", "--why=batched_cures: frozen-at-start", "--last"]
    assert ctx.launched[1:3] == [["scripts/episode/take_dq.py", "7", "--attempts"],
                                 ["scripts/episode/take_content_check.py", "7"]]
    assert len(ctx.launched) == 3                       # ONE round, no seed round before it
    after = episode_home.load_plan(ctx.book_dir, 5).shot(7).motion
    assert after != before and after.startswith("The camera")
    assert [l.action for l in ctx.learned] == ["batched_cures", "pass"]
    assert ctx.learned[0].seconds == 756.0 + 46.0 + 18.0
