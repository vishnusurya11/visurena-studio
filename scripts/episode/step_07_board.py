#!/usr/bin/env python
"""Step 07 -- board: one storyboard grid per setup on the local image model.

    uv run python scripts/episode/step_07_board.py <codex_id> <n> [--seed-bump=N] [--prompt=v1|v2]

Wraps scripts/episode/grids.py once per row of storyboard/layout.json, which
this step WRITES BY RULE from the plan (studio/grid_layout: grids of at most
nine, cols x rows == shots, 5 -> 3 + 2, faces alone when a setup mixes sizes):

    [{"setup": "pit", "cols": 3, "rows": 1, "tag": "a", "shots": [1, 2, 3]}, ...]

Nobody chooses a layout by hand any more (decision 2026-09-24-automate-the-
taste-gates); the LAYOUT gate is a rule with no ladder.  A grid already on
disk is not redrawn unless a flag asks for a redraw.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import episode_home, grid_layout, grid_room, panel_ladder, step_cli  # noqa: E402

STEP_ID = "07"
NAME = "board"
GPU = True
LAYOUT = grid_layout.FILE.as_posix()


def layout(ctx) -> list[dict]:
    """The grids to draw, by rule from the plan; nothing without a plan."""
    plan = ctx.home / "plan.json"
    if not plan.exists():
        return []
    doc = episode_home.read_json(plan)
    return grid_layout.layout(doc.get("setups") or {}, doc.get("shots") or [])


def grid_path(ctx, row: dict) -> Path:
    return ctx.home / "storyboard" / "grids" / f"{grid_layout.name_of(ctx.number, row)}.png"


def stale_names(ctx) -> set[str]:
    """The grids panels.py would refuse as drawn from an older plan -- the same
    question, asked here (ep13: 'skipped: output exists' over a changed plan)."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import panels
    drawn = panels.manifests(ctx.book_dir, ctx.number)
    if not drawn:
        return set()
    ep = episode_home.load_plan(ctx.book_dir, ctx.number)
    return set(panels.stale_grids(drawn, panels.plan_sha(ctx.book_dir, ctx.number), ep, ctx.book_dir))


def current(ctx, row: dict, stale: set[str]) -> bool:
    return grid_path(ctx, row).exists() and grid_layout.name_of(ctx.number, row) not in stale


def strays(ctx, rows: list[dict]) -> list[str]:
    """Grids on disk the layout no longer names (ep14: the grid cap split the attic
    4x2 into two 2x2s and panels.py refused 'shots drawn by two grids')."""
    names = {grid_layout.name_of(ctx.number, row) for row in rows}
    return sorted(g.stem for g in (ctx.home / "storyboard" / "grids").glob("*.png") if g.stem not in names)


def shots(ctx) -> list[dict]:
    plan = ctx.home / "plan.json"
    return list(episode_home.read_json(plan).get("shots") or []) if plan.exists() else []


def room_wanted(ctx, rows: list[dict], row: dict, shots: list[dict]) -> bool:
    """An anchor grid with siblings owes its setup a ROOM, cut from its widest
    cell, that is not older than the grid (studio/grid_room)."""
    grid = grid_path(ctx, row)
    return grid.exists() and bool(grid_room.siblings(rows, row, shots)) and grid_room.room_stale(ctx.home, row.get("setup", ""), grid)


def cut_room(ctx, row: dict, shots: list[dict]) -> None:
    anchor = grid_room.anchor_shot(shots, row["setup"])
    grid_room.cut_room(grid_path(ctx, row), row, anchor, grid_room.room_path(ctx.home, row["setup"]))


def done(ctx) -> bool:
    rows = layout(ctx)
    stale = stale_names(ctx) if rows else set()
    return (bool(rows) and all(current(ctx, row, stale) for row in rows) and not strays(ctx, rows)
            and not any(room_wanted(ctx, rows, row, shots(ctx)) for row in rows))


def run(ctx) -> None:
    rows = layout(ctx)
    if not rows:
        raise SystemExit(f"REFUSED: the plan has no shots to lay out into {LAYOUT}")
    grid_layout.write(ctx.home, rows)
    for name in strays(ctx, rows):
        panel_ladder.supersede(ctx.home / "storyboard", name)
    extra = getattr(ctx, "extra", None) or []
    stale, cells = stale_names(ctx), shots(ctx)
    # ONE ROOM PER SETUP: the anchor grid first; its room cut before any sibling
    # is drawn, and the siblings re-read as stale once the room exists.
    for row in grid_room.draw_order(rows, cells):
        if not (current(ctx, row, stale) and not extra):
            ctx.run_script("scripts/episode/grids.py", *grid_layout.argv(row), *extra, gpu=GPU, clock="grids")
        if room_wanted(ctx, rows, row, cells):
            cut_room(ctx, row, cells)
            stale = stale_names(ctx)


if __name__ == "__main__":
    raise SystemExit(step_cli.main(sys.modules[__name__], sys.argv))
