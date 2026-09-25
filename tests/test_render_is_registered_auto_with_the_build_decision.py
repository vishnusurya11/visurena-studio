"""The render approval was retired de facto by a flag typed in code.  Now it is
registered: `RENDER: auto` in gates.yaml with the build decision's id, and the
step earns the flag from the row and the ceiling, never from a literal."""
from __future__ import annotations

import json

import pytest
from PIL import Image

from scripts.episode import step_09_shoot as step
from studio import db, episode_home, eye_verdict, gate_policy
from studio.gate_policy import Policy
from studio.run_budget import EPISODE_CEILING_SECONDS, EPISODE_SHARES, Budget
from studio.stage_run import StageContext

CODEX = "20260901000001"
BUILD = "2026-09-24-episode-department"


def test_render_is_auto_with_the_build_decision_and_the_ceiling():
    row = gate_policy.of("episode", "RENDER")
    assert row.state == "auto" and row.decision == BUILD
    assert gate_policy.decided(BUILD)
    assert row.ceiling_seconds == EPISODE_CEILING_SECONDS


def test_the_flag_is_earned_from_the_row():
    assert step.approved(Policy(state="auto", decision=BUILD)) == "--approved=render"
    with pytest.raises(SystemExit, match="RENDER"):
        step.approved(Policy(state="human"))


def test_no_literal_flag_is_typed_in_the_step():
    source = open(step.__file__, encoding="utf-8").read()
    assert '"--approved=render"' not in source


@pytest.fixture()
def ctx(tmp_path):
    conn = db.get_connection(tmp_path / "t.db")
    db.init_db(conn)
    db.insert_codex(conn, "Book", codex_id=CODEX)
    book = tmp_path / "book"
    episode_home.make_rooms(book, 2)
    launched = []
    context = StageContext(conn, CODEX, book, "episode", unit="ep02", number=2,
                           logs_root=tmp_path / "logs", busy=lambda: False,
                           hold=tmp_path / "RENDER_HOLD", launch=lambda cmd: launched.append(cmd) or 0)
    context.home = episode_home.home(book, 2)
    context.launched = launched
    (context.home / "plan.json").write_text(json.dumps({"shots": [{"index": 1}]}), encoding="utf-8")
    board = context.home / "storyboard"
    board.mkdir()
    Image.new("RGB", (8, 8), (30, 30, 30)).save(board / "shot_01.png")
    for name in ("panel_dq.json", "panel_content.json"):
        episode_home.write_json(board / name, [{"shot": 1, "passed": True}])
    eye_verdict.sign(board, [board / "shot_01.png"], "pass", "fine")
    return context


def test_over_the_ceiling_the_render_is_refused_before_launch(ctx):
    now = [17_950.0]
    ctx.budget = Budget(EPISODE_CEILING_SECONDS, EPISODE_SHARES, clock=lambda: now[0])
    ctx.budget.t0 = 0.0
    with pytest.raises(SystemExit, match="ceiling"):
        step.run(ctx)
    assert ctx.launched == []


def test_under_the_ceiling_the_render_launches_with_the_earned_flag(ctx):
    ctx.budget = Budget(EPISODE_CEILING_SECONDS, EPISODE_SHARES, clock=lambda: 0.0)
    with pytest.raises(SystemExit, match="no takes"):
        step.run(ctx)
    assert "--approved=render" in ctx.launched[0]
