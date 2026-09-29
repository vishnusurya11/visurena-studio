"""One room per setup (2026-09-28): when the panel ladder redraws a setup's
ANCHOR grid, the room is cut again from it and every sibling grid is redrawn
on the new room.  ep13 redrew one grid of a setup 33 times while its siblings
kept their own rooms (the hedge LEFT in the 3x2, RIGHT in ten 1x1s)."""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from studio import episode_home, grid_layout, grid_room, panel_ladder

CODEX = "20260901000001"


class Ctx:
    def __init__(self, tmp_path):
        self.stage, self.unit, self.number, self.book_id = "episode", "ep05", 5, CODEX
        self.book_dir = tmp_path / "book"
        self.home = episode_home.home(self.book_dir, 5)
        self.launched = []

    def run_script(self, script, *extra, gpu=False, clock=None):
        """The fake render leaves a real grid on disk, as grids.py does."""
        self.launched.append([script, *extra])
        plain = [a for a in extra if not a.startswith("--")]
        row = {"setup": plain[0], "cols": int(plain[1]), "rows": int(plain[2]), "tag": plain[3] if len(plain) > 3 else ""}
        out = self.home / "storyboard" / "grids" / f"{grid_layout.name_of(self.number, row)}.png"
        out.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (256 * row["cols"], 256 * row["rows"]), (40, 40, 200)).save(out)
        return 0


def board(ctx) -> list[dict]:
    plan = {"setups": {"yard": {"described": "a yard"}},
            "shots": [{"index": 1, "setup": "yard", "size": "wide"}, {"index": 2, "setup": "yard", "size": "medium"},
                      {"index": 3, "setup": "yard", "size": "close"}]}
    ctx.home.mkdir(parents=True)
    (ctx.home / "plan.json").write_text(json.dumps(plan), encoding="utf-8")
    rows = grid_layout.layout(plan["setups"], plan["shots"])
    grid_layout.write(ctx.home, rows)
    for row in rows:
        ctx.run_script("scripts/episode/grids.py", *grid_layout.argv(row))
    ctx.launched.clear()
    return rows


def test_a_redrawn_anchor_recuts_the_room_and_redraws_its_siblings(tmp_path):
    ctx = Ctx(tmp_path)
    rows = board(ctx)
    anchor = next(r for r in rows if 1 in r["shots"])
    climb = panel_ladder.climb(ctx, rebuild=lambda: None)
    climb.redraw(anchor)
    plain = [[a for a in c[1:] if not a.startswith("--")] for c in ctx.launched]
    assert plain[0] == [a for a in grid_layout.argv(anchor) if not a.startswith("--")]
    assert len(ctx.launched) == len(rows)                       # the anchor, then every sibling
    room = grid_room.room_path(ctx.home, "yard")
    assert room.exists() and Image.open(room).size == (1024, 1024)


def test_a_redrawn_sibling_redraws_nothing_else(tmp_path):
    ctx = Ctx(tmp_path)
    rows = board(ctx)
    sibling = next(r for r in rows if 3 in r["shots"])
    panel_ladder.climb(ctx, rebuild=lambda: None).redraw(sibling)
    assert len(ctx.launched) == 1
    assert not grid_room.room_path(ctx.home, "yard").exists()
