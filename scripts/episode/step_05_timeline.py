#!/usr/bin/env python
"""Step 05 -- timeline: every shot's seconds from the measured voice.

    uv run python scripts/episode/step_05_timeline.py <codex_id> <n>

Wraps scripts/episode/respot.py then scripts/episode/timeline.py.  Done when
the timeline on disk is the timeline of THIS plan and THIS voice
(episode_home.load_placed, the one door, refuses a missing or stale one).
Free, no GPU.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pydantic import ValidationError  # noqa: E402

from studio import episode_home, speech_gap, step_cli  # noqa: E402

STEP_ID = "05"
NAME = "timeline"
GPU = False


def fresh(book: Path, number: int) -> bool:
    """Whether a timeline is on disk AND was built from the plan and voice on
    disk: load_placed is the one door, and it refuses a missing or stale one.
    A plan the contract refuses has no fresh timeline either; the run names
    that fault, `done` only answers no."""
    try:
        episode_home.load_placed(book, number, episode_home.load_plan(book, number))
    except (SystemExit, ValidationError, FileNotFoundError):
        return False                       # no plan at all: no timeline of it either
    return True


def placed_of(book: Path, number: int) -> dict:
    """The timeline to measure; an unreadable plan measures nothing here (the
    contract refuses it at its own door)."""
    try:
        return episode_home.load_placed(book, number, episode_home.load_plan(book, number))
    except (SystemExit, ValidationError, FileNotFoundError):
        return {}


def done(ctx) -> bool:
    """Fresh AND carrying no hole in speech over the wall (finding 64): a
    resume must not skip past a gap QC would refuse after the render."""
    return fresh(ctx.book_dir, ctx.number) and speech_gap.refusal(placed_of(ctx.book_dir, ctx.number)) is None


def run(ctx) -> None:
    ctx.run_script("scripts/episode/respot.py", clock="respot")
    ctx.run_script("scripts/episode/timeline.py", clock="timeline")
    if why := speech_gap.refusal(placed_of(ctx.book_dir, ctx.number)):
        raise SystemExit(why)


if __name__ == "__main__":
    raise SystemExit(step_cli.main(sys.modules[__name__], sys.argv))
