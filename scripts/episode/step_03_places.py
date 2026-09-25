#!/usr/bin/env python
"""Step 03 -- places: each setup's place picture at this unit's hour.

    uv run python scripts/episode/step_03_places.py <codex_id> <n> [--new=<loc>="Its name"]

Wraps scripts/refs/places.py --draw (the local image model).  Done when every
setup with a location has the picture its view names under refs/locations/.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import episode_home, step_cli  # noqa: E402

STEP_ID = "03"
NAME = "places"
GPU = True
ANCHOR = "wide_establishing"


def pictures(book: Path, plan: dict) -> list[Path]:
    """The place picture every setup with a location names."""
    out = []
    for setup in (plan.get("setups") or {}).values():
        if setup.get("location"):
            out.append(Path(book) / "refs" / "locations" / setup["location"]
                       / f"{setup.get('view') or ANCHOR}.png")
    return out


def done(ctx) -> bool:
    plan = ctx.home / "plan.json"
    if not plan.exists():
        return False
    return all(p.exists() for p in pictures(ctx.book_dir, episode_home.read_json(plan)))


def run(ctx) -> None:
    extra = getattr(ctx, "extra", None) or []
    ctx.run_script("scripts/refs/places.py", "--draw", *extra, gpu=GPU, clock="places")


if __name__ == "__main__":
    raise SystemExit(step_cli.main(sys.modules[__name__], sys.argv))
