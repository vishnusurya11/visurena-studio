"""Step 09 parks on nobody.  The take eye judges the kept takes after the
machine gates, a pass is signed in the judge's name, and the word Escalation
is not in the file.  The panel three-verdict refusal stays in front of the
render; the budget share is opened through the context."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from PIL import Image

from scripts.episode import step_09_shoot as step
from studio import db, episode_home, eye_verdict
from studio.learnings import Learning
from studio.run_budget import EPISODE_SHARES, Budget
from studio.stage_run import StageContext

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "tests" / "fixtures" / "episodes" / "ep05_plan.json"
CODEX = "20260901000001"


def test_the_word_escalation_is_not_in_step_09():
    source = (ROOT / "scripts" / "episode" / "step_09_shoot.py").read_text(encoding="utf-8")
    assert "Escalation" not in source and "escalate" not in source
    assert "judged_gate.clear" in source and "EYE_TAKES" in source


@pytest.fixture()
def ctx(tmp_path, monkeypatch):
    conn = db.get_connection(tmp_path / "t.db")
    db.init_db(conn)
    db.insert_codex(conn, "Book", codex_id=CODEX)
    book = tmp_path / "book"
    episode_home.make_rooms(book, 5)
    launched, opened, learned = [], [], []
    context = StageContext(conn, CODEX, book, "episode", unit="ep05", number=5,
                           logs_root=tmp_path / "logs", busy=lambda: False, hold=tmp_path / "RENDER_HOLD",
                           launch=lambda cmd: launched.append(cmd[1:]) or 0)
    context.home = episode_home.home(book, 5)
    context.extra, context.launched, context.opened, context.learned = [], launched, opened, learned
    context.budget = Budget(18000, EPISODE_SHARES, clock=lambda: 0.0)
    context.learn = lambda learning: learned.append(learning)
    context.open_step = lambda step_id: opened.append(step_id) or context.budget.start(step_id)
    shutil.copy(PLAN, context.home / "plan.json")
    board = context.home / "storyboard"
    board.mkdir(parents=True)
    Image.new("RGB", (8, 8), (30, 30, 30)).save(board / "shot_01.png")
    rows = [{"shot": s["index"], "passed": True} for s in json.loads(PLAN.read_text(encoding="utf-8"))["shots"]]
    episode_home.write_json(board / "panel_dq.json", rows)
    episode_home.write_json(board / "panel_content.json", rows)
    eye_verdict.sign(board, [board / "shot_01.png"], "pass", "clean")
    monkeypatch.setattr(step, "CLONES", lambda take: [])
    return context


def take(ctx, passing: bool = True) -> Path:
    room = ctx.home / "takes" / "r2v"
    room.mkdir(parents=True, exist_ok=True)
    t = room / "T01.mp4"
    t.write_bytes(b"take")
    gates = [{"name": "jump", "value": 0.9, "ok": passing, "hard": True, "note": "0.90", "penalty": 0.0}]
    episode_home.write_json(room / "T01.dq.json", {"file": "T01.mp4", "gates": gates, "attempts": []})
    episode_home.write_json(room / "T01.content.json", {"passed": True, "faults": []})
    episode_home.write_json(room / "shots.json", [{"index": 1, "shots": [1], "measured_seconds": 4.0, "frames": 101,
                                                   "rel_path": "episodes/ep05/takes/r2v/T01.mp4"}])
    return t


def test_a_clean_round_is_signed_by_the_judge_and_the_step_is_done(ctx):
    t = take(ctx)
    step.run(ctx)
    assert [c[0] for c in ctx.launched] == ["scripts/episode/takes_r2v.py", "scripts/episode/take_dq.py",
                                            "scripts/episode/take_content_check.py", "scripts/episode/take_strip.py"]
    doc = json.loads(eye_verdict.path(t.parent, eye_verdict.fingerprint([t])).read_text(encoding="utf-8"))
    assert doc["verdict"] == "pass" and doc["signed_by"] == "judge:take_eye@1"
    assert ctx.opened == ["09"] and ctx.learned == [] and step.done(ctx)


def test_a_fault_climbs_and_ends_flagged_never_parked(ctx):
    t = take(ctx, passing=False)
    step.run(ctx)
    doc = json.loads(eye_verdict.path(t.parent, eye_verdict.fingerprint([t])).read_text(encoding="utf-8"))
    # a narration shot, a HARD geometry fault, its passed panel on disk: the still
    assert doc["verdict"] == "flagged" and doc["terminal"] == "still"
    assert doc["faults"][0]["kind"] == "jump" and doc["faults"][0]["severity"] == "normal"
    from studio import take_ladder
    assert take_ladder.load_stills(ctx.home)[1]["panel"] == "episodes/ep05/storyboard/shot_01.png"
    assert any(isinstance(l, Learning) and l.terminal for l in ctx.learned)
    assert "--retake=1" in ctx.launched[4] and "--last" in ctx.launched[4]     # the seed round, batched
    assert (ctx.book_dir / "audit" / "rows.jsonl").exists() and step.done(ctx)


def test_the_panel_refusal_still_stands_in_front_of_the_render(ctx):
    (ctx.home / "storyboard" / "panel_dq.json").unlink()
    with pytest.raises(SystemExit, match="panel_dq.json"):
        step.run(ctx)
    assert ctx.launched == []


def test_a_content_fault_goes_to_the_judge_not_out_of_the_step(ctx):
    """ep12: take_content_check exits 1 when a take fails; run_script turned that
    into a refusal and the take judge and its ladder never ran. A checker that
    wrote every take's verdict and found faults hands them to the judge."""
    take(ctx)
    ctx.launch = lambda cmd: ctx.launched.append(cmd[1:]) or (1 if "take_content_check" in cmd[1] else 0)
    step.run(ctx)
    assert any("take_strip" in c[0] for c in ctx.launched)


def test_a_checker_that_left_a_take_unjudged_still_refuses(ctx):
    t = take(ctx)
    (t.parent / "T01.content.json").unlink()
    ctx.launch = lambda cmd: ctx.launched.append(cmd[1:]) or (1 if "take_content_check" in cmd[1] else 0)
    with pytest.raises(SystemExit, match="take_content_check"):
        step.run(ctx)
