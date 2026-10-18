"""At a cap the ladder takes its terminal and the run goes on (owner 2026-10-18).

- the step runner opens a wall per step: a timestamped `STEP <id> start` line and a
  timing.jsonl `started` row on entry, so a killed step is visible (STEP_CAPS.md finding 4);
- a judged gate takes no rung past the step's wall, nor past its row's per-episode rounds
  (persisted, so a second run of the step reads the first's count); it keeps the best,
  signs flagged and logs `CAP <phase>: r/N rounds, mm:ss, kept best (k advisories)`.
"""
from __future__ import annotations

import json
import types

from studio import db, eye_verdict as ev, judged_gate, step_attempts, step_caps, step_runner, step_wall
from studio.gate_policy import Policy
from studio.judges.verdict import Fault, Verdict
from studio.ladder import Ladder, Rung
from studio.run_budget import EPISODE_SHARES, Budget
from studio.stage_run import StageContext


class Ctx:
    def __init__(self, tmp_path, wall=None):
        self.stage, self.unit = "episode", "ep01"
        self.book_dir = tmp_path / "book"
        self.home = self.book_dir / "episodes" / "ep01"
        self.home.mkdir(parents=True, exist_ok=True)
        self.budget = Budget(18000, EPISODE_SHARES, clock=lambda: 0.0)
        self.learned, self.said, self.step_wall = [], [], wall

    def learn(self, learning):
        self.learned.append(learning)

    def log(self, msg, **kw):
        self.said.append(msg)


AUTO = Policy(state="auto", judge="take_eye@1", decision="2026-09-24-automate-the-taste-gates",
              terminal="keep_best")


def failing():
    return Verdict(judge="take_eye", version="1", passed=False, confidence=1.0, reads=3,
                   faults=[Fault(kind="lag", where="T07"), Fault(kind="warp", where="T08")])


def climb(ctx, rungs=3):
    room = ctx.home / "takes" / "r2v"
    room.mkdir(parents=True, exist_ok=True)
    (room / "T07.mp4").write_bytes(b"take")
    taken = []
    judged_gate.clear(ctx, "EYE_TAKES", judge=failing,
                      sign=lambda v: ev.sign_verdict(room, [room / "T07.mp4"], v),
                      ladder=judged_gate.Rungs(Ladder([Rung("seed", 1.0, tries=rungs)], "keep_best"),
                                               take=lambda rung, i, v: taken.append(i)),
                      terminal=lambda v: v, policy=AUTO)
    doc = json.loads(next(room.glob("eye_*.json")).read_text(encoding="utf-8"))
    return taken, doc


def test_retakes_stop_at_the_episodes_two_rounds_and_keep_the_best(tmp_path):
    ctx = Ctx(tmp_path)
    taken, doc = climb(ctx)
    assert taken == [0, 1]
    assert doc["verdict"] == "flagged" and doc["terminal"] == "keep_best"
    assert step_attempts.count(ctx.home, "retakes") == 2
    assert any(line.startswith("CAP retakes: 2/2 rounds") and "kept best (2 advisories)" in line
               for line in ctx.said)


def test_a_second_run_reads_the_first_runs_count(tmp_path):
    step_attempts.spend(Ctx(tmp_path).home, "retakes")
    step_attempts.spend(Ctx(tmp_path).home, "retakes")
    taken, doc = climb(Ctx(tmp_path))
    assert taken == [] and doc["terminal"] == "keep_best"


def test_no_rung_past_the_steps_wall(tmp_path):
    wall = step_wall.StepWall("09", 60.0, started=0.0, clock=lambda: 61.0)
    ctx = Ctx(tmp_path, wall=wall)
    taken, doc = climb(ctx)
    assert taken == [] and doc["terminal"] == "keep_best"
    assert any(line.startswith("CAP retakes: 0/2 rounds, 01:01") for line in ctx.said)


# ---- the runner ------------------------------------------------------------------------

def _runner_ctx(tmp_path):
    conn = db.get_connection(tmp_path / "t.db")
    db.init_db(conn)
    codex_id = db.insert_codex(conn, "Book", codex_id="20260901000001")
    return StageContext(conn, codex_id, tmp_path / "book", "episode", unit="ep01", number=1,
                        logs_root=tmp_path / "logs", busy=lambda: False,
                        hold=tmp_path / "RENDER_HOLD", launch=lambda cmd: 0)


def test_a_step_logs_its_start_and_writes_a_started_row(tmp_path, capsys):
    ctx, seen = _runner_ctx(tmp_path), []
    step = types.SimpleNamespace(STEP_ID="05", NAME="timeline", GPU=False,
                                 run=lambda c: seen.append(c.step_wall.wall_s), done=lambda c: False)
    assert step_runner.run_steps(ctx, [step]) == "completed"
    assert seen == [step_caps.step_wall_s("05")]
    assert "STEP 05 start" in capsys.readouterr().out
    rows = [json.loads(l) for l in (tmp_path / "book" / "episodes" / "ep01" / "timing.jsonl")
            .read_text(encoding="utf-8").splitlines()]
    assert rows[0]["stage"] == "step_05" and rows[0]["event"] == "started" and rows[0]["seconds"] == 0


def test_a_step_past_its_wall_says_cap_and_the_run_goes_on(tmp_path, capsys):
    ctx, ran = _runner_ctx(tmp_path), []
    now = [0.0]
    ctx.clock = lambda: now[0]
    late = types.SimpleNamespace(STEP_ID="05", NAME="timeline", GPU=False, done=lambda c: False,
                                 run=lambda c: now.__setitem__(0, 200.0))
    after = types.SimpleNamespace(STEP_ID="06", NAME="prompts", GPU=False, done=lambda c: False,
                                  run=lambda c: ran.append("06"))
    assert step_runner.run_steps(ctx, [late, after]) == "completed"
    assert ran == ["06"]
    assert "CAP step 05: 1/1 rounds, 03:20" in capsys.readouterr().out


def test_a_ladder_whose_rungs_end_at_the_cap_still_says_cap(tmp_path):
    """Jekyll Kawajiri ep01 (2026-10-18): the plan ladder has exactly its three rounds of rungs;
    it ran out of rungs AT the cap, kept best twice, and the log held no CAP line."""
    ctx = Ctx(tmp_path)
    taken, doc = climb(ctx, rungs=2)
    assert taken == [0, 1] and doc["terminal"] == "keep_best"
    assert sum(line.startswith("CAP retakes: 2/2 rounds") for line in ctx.said) == 1
