#!/usr/bin/env python
"""Step 04 -- record: every line in its character's voice, measured and listened to.

    uv run python scripts/episode/step_04_record.py <codex_id> <n> [--redo=3,4]

Wraps scripts/episode/say_lines.py (local TTS + the ear, GPU) and then
scripts/episode/speaker_check.py (one speaker, one voice; CPU).  Done when
lines.json carries every line the plan names and the spread report exists.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import episode_home, step_cli  # noqa: E402

STEP_ID = "04"
NAME = "record"
GPU = True


def rendered(plan: dict, rows: list[dict]) -> bool:
    """Whether every line the plan names has a measured row."""
    have = {r.get("index") for r in rows}
    return all(line.get("index") in have for line in plan.get("lines") or [])


def done(ctx) -> bool:
    plan, sheet = ctx.home / "plan.json", ctx.home / "audio" / "lines" / "lines.json"
    spread = ctx.home / "review" / "speaker_check.json"
    if not (plan.exists() and sheet.exists() and spread.exists()):
        return False
    return rendered(episode_home.read_json(plan), episode_home.read_json(sheet))


def voiceless(ctx) -> list[str]:
    """This plan's speakers with no design clip at book level: cast them first,
    just in time, so the line never waits on the bible for a voice."""
    from studio import cast_home
    plan = episode_home.read_json(ctx.home / "plan.json")
    who = {line.get("speaker") or line.get("who") for line in plan.get("lines") or []}
    return sorted(w for w in who if w and not cast_home.clip(ctx.book_dir, w).exists())


def run(ctx) -> None:
    if missing := voiceless(ctx):
        ctx.run_script("scripts/cast/cast_voices.py", f"--only={','.join(missing)}", gpu=GPU, clock="cast")
    extra = getattr(ctx, "extra", None) or []
    ctx.run_script("scripts/episode/say_lines.py", *extra, gpu=GPU, clock="lines")
    ctx.run_script("scripts/episode/speaker_check.py", clock="speaker_check")


if __name__ == "__main__":
    raise SystemExit(step_cli.main(sys.modules[__name__], sys.argv))
