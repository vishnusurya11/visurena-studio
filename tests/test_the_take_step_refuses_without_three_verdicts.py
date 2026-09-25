"""The take step refuses to render unless the panels carry all three verdicts:
the statistics (panel_dq.json), the picture's content (panel_content.json)
and the eye (storyboard/eye_<sha8>.json signed for these exact panels).
Nothing is launched until all three are there."""
from __future__ import annotations

import json

import pytest
from PIL import Image

from scripts.episode import step_09_shoot as step
from studio import db, episode_home, eye_verdict
from studio.escalate import Escalation
from studio.stage_run import StageContext

CODEX = "20260901000001"


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
    return context


def _verdict(ctx, name):
    episode_home.write_json(ctx.home / "storyboard" / name, [{"shot": 1, "passed": True}])


def test_no_verdict_at_all_names_all_three(ctx):
    with pytest.raises(SystemExit, match="panel_dq.json") as got:
        step.run(ctx)
    assert "panel_content.json" in str(got.value) and "eye" in str(got.value)
    assert ctx.launched == []


def test_two_machine_verdicts_without_the_eye_still_refuse(ctx):
    _verdict(ctx, "panel_dq.json")
    _verdict(ctx, "panel_content.json")
    with pytest.raises(SystemExit, match="eye") as got:
        step.run(ctx)
    assert "panel_dq.json" not in str(got.value)
    assert ctx.launched == []


def test_an_eye_signed_for_other_panels_does_not_count(ctx):
    _verdict(ctx, "panel_dq.json")
    _verdict(ctx, "panel_content.json")
    board = ctx.home / "storyboard"
    eye_verdict.sign(board, [board / "shot_01.png"], "pass", "fine")
    Image.new("RGB", (8, 8), (90, 90, 90)).save(board / "shot_01.png")   # redrawn after the signature
    with pytest.raises(SystemExit, match="eye"):
        step.run(ctx)
    assert ctx.launched == []


def test_a_failed_machine_verdict_refuses_by_name(ctx):
    episode_home.write_json(ctx.home / "storyboard" / "panel_dq.json", [{"shot": 1, "passed": False}])
    _verdict(ctx, "panel_content.json")
    with pytest.raises(SystemExit, match="panel_dq.json.*failed"):
        step.run(ctx)


def test_all_three_verdicts_let_the_render_start(ctx):
    _verdict(ctx, "panel_dq.json")
    _verdict(ctx, "panel_content.json")
    board = ctx.home / "storyboard"
    eye_verdict.sign(board, [board / "shot_01.png"], "pass", "fine")
    with pytest.raises(SystemExit, match="no takes"):    # the fake render leaves nothing on disk
        step.run(ctx)
    assert ctx.launched[0][1] == "scripts/episode/takes_r2v.py"
    assert len(ctx.launched) == 4
