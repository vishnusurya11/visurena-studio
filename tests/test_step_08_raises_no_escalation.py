"""Step 08 parks on nobody.  After the panels, both machine gates and the
contact sheet, `judged_gate.clear` runs the panel eye on EYE_PANELS; a pass is
signed in the judge's name, the budget share is opened through the context,
and neither Escalation nor a `require` of a human eye is in the file."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from PIL import Image

from scripts.episode import step_08_panels as step
from studio import db, episode_home, eye_verdict
from studio.judges.verdict import Verdict
from studio.run_budget import EPISODE_SHARES, Budget
from studio.stage_run import StageContext

ROOT = Path(__file__).resolve().parents[1]
CODEX = "20260901000001"
PLAN = {"setups": {"yard": {"described": "a yard"}},
        "shots": [{"index": 1, "setup": "yard", "size": "wide"}, {"index": 2, "setup": "yard", "size": "wide"}]}


def test_the_words_escalation_and_require_are_not_in_step_08():
    source = (ROOT / "scripts" / "episode" / "step_08_panels.py").read_text(encoding="utf-8")
    assert "Escalation" not in source and "escalate" not in source
    assert "require(" not in source and "sign_eye" not in source
    assert "judged_gate.clear" in source and "EYE_PANELS" in source and "open_step" in source


@pytest.fixture()
def ctx(tmp_path):
    conn = db.get_connection(tmp_path / "t.db")
    db.init_db(conn)
    db.insert_codex(conn, "Book", codex_id=CODEX)
    book = tmp_path / "book"
    launched, opened, learned = [], [], []
    context = StageContext(conn, CODEX, book, "episode", unit="ep04", number=4,
                           logs_root=tmp_path / "logs", busy=lambda: False, hold=tmp_path / "RENDER_HOLD",
                           launch=lambda cmd: launched.append(cmd[1:]) or 0)
    context.home = episode_home.home(book, 4)
    context.extra, context.launched, context.opened, context.learned = [], launched, opened, learned
    context.budget = Budget(18000, EPISODE_SHARES, clock=lambda: 0.0)
    context.learn = lambda learning: learned.append(learning)
    context.open_step = lambda step_id: opened.append(step_id) or context.budget.start(step_id)
    board = context.home / "storyboard"
    board.mkdir(parents=True)
    (context.home / "plan.json").write_text(json.dumps(PLAN), encoding="utf-8")
    for i in (1, 2):
        Image.new("RGB", (8, 8), (i * 20, 0, 0)).save(board / f"shot_{i:02d}.png")
    rows = [{"shot": 1, "passed": True}, {"shot": 2, "passed": True}]
    episode_home.write_json(board / "panel_dq.json", rows)
    episode_home.write_json(board / "panel_content.json", rows)
    return context


def passing():
    return Verdict(judge="panel_eye", version="1", passed=True, confidence=1.0, reads=2)


def test_the_step_runs_the_chain_then_the_judge_signs(ctx, monkeypatch):
    monkeypatch.setattr(step, "judge_of", lambda ctx: passing)
    step.run(ctx)
    assert [c[0] for c in ctx.launched] == ["scripts/episode/panels.py", "scripts/episode/panel_check.py"]
    assert ctx.opened == ["08"]
    board = ctx.home / "storyboard"
    panels = sorted(board.glob("shot_*.png"))
    assert (board / "contact.png").exists()
    doc = json.loads(eye_verdict.path(board, eye_verdict.fingerprint(panels)).read_text(encoding="utf-8"))
    assert doc["verdict"] == "pass" and doc["signed_by"] == "judge:panel_eye@1"
    assert step.done(ctx) and step.panel_refusals(ctx.home) == [] and [l.action for l in ctx.learned] == ["pass"]


def test_a_stale_content_verdict_sends_the_panels_back_through_the_vision_gate(ctx, monkeypatch):
    monkeypatch.setattr(step, "judge_of", lambda ctx: passing)
    (ctx.home / "storyboard" / "panel_content.json").unlink()
    step.run(ctx)
    assert [c[0] for c in ctx.launched] == ["scripts/episode/panels.py", "scripts/episode/panel_check.py",
                                           "scripts/episode/panel_content_check.py"]


def test_the_default_judge_reads_the_plan_afresh_on_every_call(ctx, monkeypatch):
    seen = []
    monkeypatch.setattr(step.panel_eye, "judge", lambda home, plan, **kw: seen.append(plan) or passing())
    monkeypatch.setattr(step.panel_eye, "tools", lambda: {})
    judge = step.judge_of(ctx)
    judge()
    (ctx.home / "plan.json").write_text(json.dumps({**PLAN, "shots": PLAN["shots"][:1]}), encoding="utf-8")
    judge()
    assert [len(p["shots"]) for p in seen] == [2, 1]
