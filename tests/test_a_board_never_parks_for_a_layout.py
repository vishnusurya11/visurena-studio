"""Step 07 parks on nobody: without a layout.json it writes one by rule from the
plan and draws every grid, naming each grid's shots; the word Escalation is
not in the file."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.episode import step_07_board as step
from studio import db, episode_home, grid_layout
from studio.stage_run import StageContext

ROOT = Path(__file__).resolve().parents[1]
CODEX = "20260901000001"
PLAN = {"setups": {"yard": {"described": "a yard"}, "room": {"described": "a room"}},
        "shots": [{"index": i, "setup": "yard", "size": "wide"} for i in range(1, 6)]
                 + [{"index": 6, "setup": "room", "size": "close"}, {"index": 7, "setup": "room", "size": "wide"}]}


def test_the_word_escalation_is_not_in_step_07():
    source = (ROOT / "scripts" / "episode" / "step_07_board.py").read_text(encoding="utf-8")
    assert "Escalation" not in source and "escalate" not in source
    assert "grid_layout" in source


@pytest.fixture()
def ctx(tmp_path):
    conn = db.get_connection(tmp_path / "t.db")
    db.init_db(conn)
    db.insert_codex(conn, "Book", codex_id=CODEX)
    book = tmp_path / "book"
    launched = []
    context = StageContext(conn, CODEX, book, "episode", unit="ep04", number=4,
                           logs_root=tmp_path / "logs", busy=lambda: False, hold=tmp_path / "RENDER_HOLD",
                           launch=lambda cmd: launched.append(cmd[1:]) or 0)
    context.home = episode_home.home(book, 4)
    context.extra, context.launched = [], launched
    context.home.mkdir(parents=True)
    (context.home / "plan.json").write_text(json.dumps(PLAN), encoding="utf-8")
    return context


def test_the_board_writes_the_layout_by_rule_and_draws_every_grid(ctx):
    assert not step.done(ctx)
    step.run(ctx)
    assert ctx.launched == [
        ["scripts/episode/grids.py", CODEX, "4", "yard", "3", "1", "a", "--shots=1,2,3"],
        ["scripts/episode/grids.py", CODEX, "4", "yard", "2", "1", "b", "--shots=4,5"],
        ["scripts/episode/grids.py", CODEX, "4", "room", "1", "1", "--shots=7"],
        ["scripts/episode/grids.py", CODEX, "4", "room", "1", "1", "s06", "--shots=6"]]
    assert grid_layout.read(ctx.home) == grid_layout.layout(PLAN["setups"], PLAN["shots"])


def test_a_grid_on_disk_is_not_redrawn_and_the_step_is_done_with_all_of_them(ctx):
    for row in grid_layout.layout(PLAN["setups"], PLAN["shots"]):
        path = ctx.home / "storyboard" / "grids" / f"{grid_layout.name_of(4, row)}.png"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"grid")
    step.run(ctx)
    assert ctx.launched == [] and step.done(ctx)


def test_a_plan_with_no_shots_is_refused_not_parked(ctx):
    (ctx.home / "plan.json").write_text(json.dumps({"setups": {}, "shots": []}), encoding="utf-8")
    with pytest.raises(SystemExit, match="no shots"):
        step.run(ctx)
