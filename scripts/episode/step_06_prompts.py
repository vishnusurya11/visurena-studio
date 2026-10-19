#!/usr/bin/env python
"""Step 06 -- prompts: every take prompt built and linted before any picture.

    uv run python scripts/episode/step_06_prompts.py <codex_id> <n>

Wraps scripts/episode/takes_r2v.py --from-refs --prompts (the take-path lint,
$0, no GPU) then scripts/episode/no_last_frame.py (no last frame anywhere).
Done when takes/r2v/prompts.json is newer than the plan and the measured
lines -- the two things the timeline, and so every prompt, is derived from.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import step_cli  # noqa: E402

STEP_ID = "06"
NAME = "prompts"
GPU = False


def newer_than(target: Path, *sources: Path) -> bool:
    """Whether `target` exists and postdates every source (each of which must exist)."""
    if not target.exists() or not all(s.exists() for s in sources):
        return False
    return all(target.stat().st_mtime >= s.stat().st_mtime for s in sources)


def done(ctx) -> bool:
    return newer_than(ctx.home / "takes" / "r2v" / "prompts.json",
                      ctx.home / "plan.json", ctx.home / "audio" / "lines" / "lines.json")


def camera_advisories(plan: dict) -> list[str]:
    """`shot 1: the aim 'the left third' is a layout word, not a thing` for each writer camera
    head camera_lint would refuse as cure text -- said, never walled: the lint was calibrated on
    cure-written heads, not the writer's (timeline debate 2026-10-18, P1)."""
    from studio import camera_lint
    return [f"shot {s.get('index')}: {f}" for s in plan.get("shots") or []
            for f in camera_lint.faults(str(s.get("motion") or ""))]


def run(ctx) -> None:
    ctx.run_script("scripts/episode/takes_r2v.py", "--from-refs", "--prompts", clock="prompts")
    ctx.run_script("scripts/episode/no_last_frame.py", clock="no_last_frame")
    # the grid prompts linted before any grid is drawn: step 07's own wall, dry, no GPU (P1)
    ctx.run_script("scripts/episode/grids.py", "--prompts", clock="grid_lint")
    import json
    plan = json.loads((ctx.home / "plan.json").read_text(encoding="utf-8"))
    for said in camera_advisories(plan):
        ctx.log(f"camera advisory {said}")


if __name__ == "__main__":
    raise SystemExit(step_cli.main(sys.modules[__name__], sys.argv))
