#!/usr/bin/env python
"""Step 10 -- edit: the title card, then the cut to the measured voice.

    uv run python scripts/episode/step_10_edit.py <codex_id> <n> [--engine=r2v] [--bed=<model>]

Wraps scripts/episode/series_title.py (skipped once title/epNN.mp4 exists)
then scripts/episode/assemble.py --engine=r2v.  assemble keeps every cut as
cut/master_iterN.mp4 and never overwrites one; the step is done when the
engine's master exists.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import episode_home, step_cli  # noqa: E402

STEP_ID = "10"
NAME = "edit"
GPU = True
ENGINE = "r2v"


def engine_of(extra: list[str]) -> str:
    """`--engine=` when typed, else the house engine."""
    return next((a.split("=", 1)[1] for a in extra if a.startswith("--engine=")), ENGINE)


def engine_flags(extra: list[str]) -> list[str]:
    """The engine flag first, then every other flag as typed."""
    return [f"--engine={engine_of(extra)}", *[a for a in extra if not a.startswith("--engine=")]]


def title_clip(ctx) -> Path:
    return ctx.book_dir / "title" / f"ep{ctx.number:02d}.mp4"


def done(ctx) -> bool:
    engine = engine_of(getattr(ctx, "extra", None) or [])
    return title_clip(ctx).exists() and episode_home.master_path(ctx.book_dir, ctx.number, engine).exists()


def run(ctx) -> None:
    extra = getattr(ctx, "extra", None) or []
    if not title_clip(ctx).exists():
        ctx.run_script("scripts/episode/series_title.py", gpu=GPU, clock="title")
    ctx.run_script("scripts/episode/assemble.py", *engine_flags(extra), gpu=GPU, clock="assemble")


if __name__ == "__main__":
    raise SystemExit(step_cli.main(sys.modules[__name__], sys.argv))
