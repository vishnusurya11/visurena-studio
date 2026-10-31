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

from studio import boundary, episode_home, grid_layout, grid_room, pack_refs, panel_ladder, qwen21_edit, step_cli  # noqa: E402

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
    return grid_layout.layout(doc.get("setups") or {}, doc.get("shots") or [], needs_of(ctx.book_dir, doc))


def needs_of(book: Path, doc: dict) -> dict[int, set]:
    """What each shot stages: its faces and the setup props its prose names."""
    setups = doc.get("setups") or {}
    return {int(s["index"]): set(s.get("faces") or []) | named_props(book, setups.get(s["setup"]) or {}, s)
            for s in doc.get("shots") or []}


def named_props(book: Path, setup: dict, shot: dict) -> set:
    text = " ".join(shot.get(k) or "" for k in ("frame", "motion", "at_rest"))
    return {pid for pid in setup.get("props") or [] if pack_refs.props_named(book, [pid], text)}


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
    room = grid_room.room_path(ctx.home, row["setup"])
    grid_room.recut_room(grid_path(ctx, row), row, anchor, room, empty=room_emptier(ctx))
    if not grid_room.emptied(room):
        ctx.log(f"room {row['setup']}: people left after {grid_room.EMPTY_TRIES} edits; no take stages it",
                step_id=STEP_ID, level="WARNING")


EDIT = qwen21_edit.WORKFLOW
"""The one-picture edit on Qwen-Image 2.1 (studio/qwen21_edit; Qwen-Image-Edit 2511 until 2026-10-30)."""


def edit_room(prompt: str, source: Path, target: Path, seed: int) -> None:
    qwen21_edit.edit(prompt, source, target, seed, prefix="room_empty")


def people_in(path: Path) -> int:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import panel_content_check
    return panel_content_check.read(path).people


def room_emptier(ctx):
    """path -> people left: the cut room edited empty on the GPU, read back by the panel reader."""
    return lambda path: grid_room.empty_room(path, edit_room, people_in)


def rendered(ctx) -> bool:
    """Takes on disk: the board has been shot from.  A prompt-builder change
    after that must not walk a resume back into a redraw (ep14, 2026-09-28:
    the geometry fields and the room made every rendered grid read as stale
    under 30 rendered takes) -- the plan's own report-mode rule."""
    return any((ctx.home / "takes" / "r2v").glob("T??.mp4"))


def shot_from(ctx, row: dict) -> bool:
    """The grid, or a superseded version of it: the panel ladder moves a grid
    aside when it redraws, and a redraw that never landed leaves only the
    versions (ep20 3x1_b, 2026-10-08: four relaunches each re-drew and
    re-judged the same grid under 28 rendered takes)."""
    if grid_path(ctx, row).exists():
        return True
    name = grid_layout.name_of(ctx.number, row)
    return any((ctx.home / "storyboard" / "superseded").glob(f"{name}_v*.png"))


def done(ctx) -> bool:
    rows = layout(ctx)
    if rows and rendered(ctx):
        return all(shot_from(ctx, row) for row in rows)
    stale = stale_names(ctx) if rows else set()
    return (bool(rows) and all(current(ctx, row, stale) for row in rows) and not strays(ctx, rows)
            and not any(room_wanted(ctx, rows, row, shots(ctx)) for row in rows))


def owner_ordered(ctx) -> bool:
    """The owner ordered this step redone (a pending redo row): the stale grids are redrawn even under
    rendered takes (Jekyll ep06, 2026-10-29: Poole's redrawn sheet; the guard returned at once)."""
    from studio import work_orders
    conn = getattr(ctx, "conn", None)
    return conn is not None and STEP_ID in work_orders.redo_steps(conn, ctx.codex_id, ctx.stage, ctx.unit or "book")


def run(ctx) -> None:
    rows = layout(ctx)
    if not rows:
        raise SystemExit(f"REFUSED: the plan has no shots to lay out into {LAYOUT}")
    if rendered(ctx) and all(grid_path(ctx, row).exists() for row in rows) and not owner_ordered(ctx):
        ctx.log("the board's takes are rendered: no grid is redrawn under them", step_id=STEP_ID, level="WARNING")
        return
    grid_layout.write(ctx.home, rows)
    for name in strays(ctx, rows):
        panel_ladder.supersede(ctx.home / "storyboard", name)
    extra = getattr(ctx, "extra", None) or []
    stale, cells = stale_names(ctx), shots(ctx)
    # ONE ROOM PER SETUP: the anchor grid first; its room cut before any sibling
    # is drawn, and the siblings re-read as stale once the room exists.
    for row in grid_room.draw_order(rows, cells):
        if not (current(ctx, row, stale) and not extra):
            boundary.check(ctx.home, f"step 07 before grid {row}")     # C3_verdict #7
            ctx.run_script("scripts/episode/grids.py", *grid_layout.argv(row), *extra, gpu=GPU, clock="grids")
        if room_wanted(ctx, rows, row, cells):
            cut_room(ctx, row, cells)
            stale = stale_names(ctx)


if __name__ == "__main__":
    raise SystemExit(step_cli.main(sys.modules[__name__], sys.argv))
