#!/usr/bin/env python
"""Step 07 -- board: one storyboard grid per setup on the local image model.

    uv run python scripts/episode/step_07_board.py <codex_id> <n> [--shots=1,2] [--seed-bump=N] [--prompt=v1|v2]

Wraps scripts/episode/grids.py once per row of storyboard/layout.json:

    [{"setup": "pit", "cols": 3, "rows": 2, "tag": ""}, ...]

The layout rule (which shots share a grid, the minimum grid) is an open owner
decision, so without the file the step parks the unit and asks for one.  A
grid already on disk is not redrawn unless a flag asks for a redraw.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.episode import grids  # noqa: E402
from studio import episode_home, step_cli  # noqa: E402
from studio.escalate import Escalation  # noqa: E402

STEP_ID = "07"
NAME = "board"
GPU = True
LAYOUT = "storyboard/layout.json"


def layout(ctx) -> list[dict]:
    """The grids to draw, or an empty list when nobody has chosen them."""
    path = ctx.home / LAYOUT
    return list(episode_home.read_json(path)) if path.exists() else []


def argv_of(row: dict) -> list[str]:
    """`<setup> <cols> <rows> [tag]`, the way grids.py reads them."""
    args = [str(row["setup"]), str(int(row["cols"])), str(int(row["rows"]))]
    return args + ([str(row["tag"])] if row.get("tag") else [])


def grid_path(ctx, row: dict) -> Path:
    name = grids.grid_name(ctx.number, row["setup"], int(row["cols"]), int(row["rows"]), row.get("tag") or "")
    return grids.grids_dir(ctx.book_dir, ctx.number) / f"{name}.png"


def done(ctx) -> bool:
    rows = layout(ctx)
    return bool(rows) and all(grid_path(ctx, row).exists() for row in rows)


def run(ctx) -> None:
    rows = layout(ctx)
    if not rows:
        raise Escalation("PLAN", LAYOUT, "choose cols x rows per setup: [{setup, cols, rows, tag?}]")
    extra = getattr(ctx, "extra", None) or []
    for row in rows:
        if grid_path(ctx, row).exists() and not extra:
            continue
        ctx.run_script("scripts/episode/grids.py", *argv_of(row), *extra, gpu=GPU, clock="grids")


if __name__ == "__main__":
    raise SystemExit(step_cli.main(sys.modules[__name__], sys.argv))
