"""Step 07 parks on nobody: without a layout.json it writes one by rule from the
plan and draws every grid, naming each grid's shots; the word Escalation is
not in the file."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from PIL import Image

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
        Image.new("RGB", (256 * row["cols"], 256 * row["rows"]), "white").save(path)
    step.run(ctx)
    assert ctx.launched == [] and step.done(ctx)
    assert (ctx.home / "storyboard" / "anchors" / "yard.png").exists()   # the room, cut at no GPU cost


def test_a_plan_with_no_shots_is_refused_not_parked(ctx):
    (ctx.home / "plan.json").write_text(json.dumps({"setups": {}, "shots": []}), encoding="utf-8")
    with pytest.raises(SystemExit, match="no shots"):
        step.run(ctx)


def test_a_grid_the_layout_no_longer_names_is_superseded(ctx):
    """ep14 (2026-09-28): the grid cap split the attic 4x2 into two 2x2s; the old
    4x2 stayed in grids/ and panels.py refused 'shots drawn by two grids'."""
    grids = ctx.home / "storyboard" / "grids"
    grids.mkdir(parents=True)
    for ext in ("png", "json", "txt"):
        (grids / f"ep04_grid_yard_5x1.{ext}").write_text("old", encoding="utf-8")
    step.run(ctx)
    assert not list(grids.glob("ep04_grid_yard_5x1.*"))
    assert (ctx.home / "storyboard" / "superseded" / "ep04_grid_yard_5x1_v1.png").exists()


def test_the_anchor_grid_is_drawn_first_and_its_room_is_cut_before_the_siblings(ctx):
    """One room per setup (2026-09-28): the grid holding the widest shot leads,
    its widest cell becomes storyboard/anchors/<setup>.png, and the siblings
    are drawn after it (they stage that room)."""
    plan = {"setups": {"yard": {"described": "a yard"}},
            "shots": [{"index": i, "setup": "yard", "size": "medium"} for i in range(1, 4)]
                     + [{"index": 4, "setup": "yard", "size": "wide"}, {"index": 5, "setup": "yard", "size": "medium"}]}
    (ctx.home / "plan.json").write_text(json.dumps(plan), encoding="utf-8")

    def draw(cmd):
        ctx.launched.append(cmd[1:])
        plain = [a for a in cmd[1:] if not a.startswith("--")]
        row = {"setup": plain[3], "cols": int(plain[4]), "rows": int(plain[5]), "tag": plain[6]}
        out = ctx.home / "storyboard" / "grids" / f"{grid_layout.name_of(4, row)}.png"
        out.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (1024 * row["cols"], 1024 * row["rows"]), "white").save(out)
        return 0
    ctx.launch = draw
    step.run(ctx)
    assert [c[4] for c in ctx.launched] == ["2", "3"]          # the 2x1 (shots 4, 5) before the 3x1
    assert (ctx.home / "storyboard" / "anchors" / "yard.png").exists()
