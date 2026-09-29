#!/usr/bin/env python
"""Step 03b -- cells: every shot's at_rest and every setup's geometry, written
FROM the drawn place picture.

    uv run python scripts/episode/step_03b_cells.py <codex_id> <n>

The skill's rule -- "write cells from the drawn picture, after it exists, never
before" -- was inverted by the registry order (02 plan -> 03 places, 2026-09-24):
the writer had no picture and ep14's attic cells described a street.  This step
runs after 03: the local vision model lists each place picture's fixed things
by frame third and band (studio/picture_read); code rewrites the cells in the
idiom that held the room (studio/cells_from_picture); the battery re-judges the
plan; the plan verdict is re-signed for the new bytes with the same faults and
flag.  A plan the battery then refuses keeps the writer's cells and logs why:
this step never parks and never leaves a plan worse than it found it.
Done when storyboard/cells_from_picture.json names the plan's current sha8.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import cells_from_picture as cells, episode_home, pack_refs, picture_read, plan_verdict, step_cli  # noqa: E402
from studio.judges import verdict as jv  # noqa: E402

STEP_ID = "03b"
NAME = "cells"
GPU = True
MARK = Path("storyboard") / "cells_from_picture.json"
PLAN_CHECK = "scripts/episode/plan_check.py"
READ = None
"""A reader for tests; None is the local vision model (picture_read.read)."""
CHECK = None
"""The battery for tests; None launches plan_check as every later step reads the plan."""


def pictures(book: Path, doc: dict) -> dict[str, Path]:
    """Each setup's place picture, when it names a location that is drawn."""
    out = {}
    for name, setup in (doc.get("setups") or {}).items():
        if not setup.get("location"):
            continue
        try:
            out[name] = pack_refs.location_view(book, setup["location"], view=setup.get("view") or "")
        except SystemExit:
            continue
    return out


def stamp(home: Path) -> dict:
    mark = Path(home) / MARK
    return episode_home.read_json(mark) if mark.exists() else {}


def done(ctx) -> bool:
    plan = ctx.home / "plan.json"
    return plan.exists() and stamp(ctx.home).get("plan_sha8") == plan_verdict.plan_sha8(plan)


def resign(plan: Path, previous: dict | None) -> None:
    """The same verdict, bound to the plan's new bytes."""
    if not previous:
        return
    plan_verdict.sign(plan, f"{previous.get('note', '')} · cells from the picture (03b)".strip(" ·"),
                      signed_by=previous.get("signed_by", jv.OWNER), faults=previous.get("faults"),
                      flagged=bool(previous.get("flagged", False)))


def battery(ctx) -> tuple[int, str]:
    return CHECK(ctx) if CHECK else ctx.capture_script(PLAN_CHECK)


def apply(ctx, plan: Path, doc: dict, readings: dict) -> bool:
    """The rewritten plan kept only when the contract and the battery accept it."""
    before, previous = plan.read_bytes(), plan_verdict.read(plan)
    try:
        episode_home.write_plan(plan, cells.rewrite(doc, readings))
    except SystemExit as refused:
        ctx.log(f"the picture's cells failed the contract; the writer's kept:\n{refused}", step_id=STEP_ID, level="WARNING")
        return False
    rc, out = battery(ctx)
    if rc:
        plan.write_bytes(before)
        ctx.log(f"the picture's cells failed the battery; the writer's kept:\n{out[-1500:]}", step_id=STEP_ID, level="WARNING")
        return False
    resign(plan, previous)
    return True


def run(ctx) -> None:
    plan = ctx.home / "plan.json"
    if not plan.exists():
        raise SystemExit("REFUSED: no plan.json to write cells for")
    doc = episode_home.read_json(plan)
    read = READ or picture_read.read
    readings = {name: read(path) for name, path in pictures(ctx.book_dir, doc).items()}
    kept = apply(ctx, plan, doc, {k: v for k, v in readings.items() if v}) if any(readings.values()) else False
    for name, things in readings.items():
        ctx.log(f"  {name}: {len(things)} fixed things read" + ("" if things else " (unreadable: the writer's cells stand)"),
                step_id=STEP_ID)
    episode_home.write_json(ctx.home / MARK, {"plan_sha8": plan_verdict.plan_sha8(plan), "from_picture": kept,
                                              "readings": readings})


if __name__ == "__main__":
    raise SystemExit(step_cli.main(sys.modules[__name__], sys.argv))
