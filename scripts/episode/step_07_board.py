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

from studio import episode_home, grid_layout, step_cli  # noqa: E402

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


def done(ctx) -> bool:
    rows = layout(ctx)
    return bool(rows) and all(grid_path(ctx, row).exists() for row in rows)


def run(ctx) -> None:
    rows = layout(ctx)
    if not rows:
        raise SystemExit(f"REFUSED: the plan has no shots to lay out into {LAYOUT}")
    grid_layout.write(ctx.home, rows)
    extra = getattr(ctx, "extra", None) or []
    for row in rows:
        if grid_path(ctx, row).exists() and not extra:
            continue
        ctx.run_script("scripts/episode/grids.py", *grid_layout.argv(row), *extra, gpu=GPU, clock="grids")


if __name__ == "__main__":
    raise SystemExit(step_cli.main(sys.modules[__name__], sys.argv))
