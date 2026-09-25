#!/usr/bin/env python
"""Step 09 -- shoot: the takes, their two gates, the strip, and the eye.

    uv run python scripts/episode/step_09_shoot.py <codex_id> <n> [--retake=3,4 --why="..."] [--last]

Refuses unless the panels carry all three verdicts (panel_dq.json,
panel_content.json, a current eye).  The render approval is the RENDER row
of gates.yaml (auto, decision 2026-09-24-episode-department) and the
episode's time ceiling: `can_afford` before the render, never a flag typed
by hand.  Then wraps, in order: scripts/episode/takes_r2v.py --from-refs
--no-ends (the slow one), take_dq.py, take_content_check.py, take_strip.py;
and asks for the eye on the kept takes: takes/r2v/eye_<sha8>.json.  One GPU,
one stage: every GPU script waits for the queue.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.episode.step_08_panels import panel_refusals  # noqa: E402
from studio import episode_clock, eye_verdict, gate_policy, step_cli  # noqa: E402
from studio.run_budget import EPISODE_CEILING_SECONDS, EPISODE_SHARES, Budget  # noqa: E402

STEP_ID = "09"
NAME = "shoot"
GPU = True
TAKES = Path("takes") / "r2v"
RENDER = "render"
"""The approval kind takes_r2v.py demands on its argv."""
ASK = ("look at reports/strip_*.png; sign with "
       "scripts/episode/sign_eye.py <codex_id> <n> takes pass|fault \"<what was seen>\"")


def takes_of(take_dir: Path) -> list[Path]:
    """The kept takes (never a displaced attempt)."""
    return sorted(Path(take_dir).glob("T??.mp4"))


def judged(takes: list[Path]) -> bool:
    """Whether every kept take carries both machine verdicts."""
    return all(t.with_suffix(".dq.json").exists() and t.with_suffix(".content.json").exists()
               for t in takes)


def done(ctx) -> bool:
    takes = takes_of(ctx.home / TAKES)
    return bool(takes) and judged(takes) and eye_verdict.passed(ctx.home / TAKES, takes)


def approved(policy: gate_policy.Policy) -> str:
    """The render flag, earned from the RENDER row: registered auto with its
    decision id, so no person types it and the ceiling is the brake."""
    if policy.state != "auto":
        raise SystemExit(f"REFUSED: RENDER is {policy.state} in gates.yaml; nobody signs a render by hand")
    return f"--approved={RENDER}"


def affordable(ctx) -> tuple[bool, float, float]:
    """(can the render run, what it costs, what the ceiling leaves this step)."""
    budget = getattr(ctx, "budget", None) or Budget(EPISODE_CEILING_SECONDS, EPISODE_SHARES)
    budget.start(STEP_ID)
    cost = episode_clock.stage_norm("takes", episode_clock.conditions(ctx.book_dir, ctx.number))
    return budget.can_afford(STEP_ID, cost), cost, budget.remaining(STEP_ID)


def run(ctx) -> None:
    if why := panel_refusals(ctx.home):
        raise SystemExit("REFUSED: the takes wait on the panels: " + "; ".join(why))
    flag = approved(gate_policy.of(ctx.stage, "RENDER"))
    ok, cost, left = affordable(ctx)
    if not ok:
        raise SystemExit(f"REFUSED: the takes want {cost:.0f} s and the episode ceiling leaves "
                         f"{left:.0f} s; a run over the ceiling takes terminal rungs, not renders")
    extra = getattr(ctx, "extra", None) or []
    ctx.run_script("scripts/episode/takes_r2v.py", "--from-refs", "--no-ends", flag,
                   *extra, gpu=GPU, clock="takes")
    ctx.run_script("scripts/episode/take_dq.py", gpu=GPU, clock="take_dq")
    ctx.run_script("scripts/episode/take_content_check.py", gpu=GPU, clock="take_content")
    ctx.run_script("scripts/episode/take_strip.py", clock="strip")
    takes = takes_of(ctx.home / TAKES)
    if not takes:
        raise SystemExit(f"REFUSED: no takes under {TAKES.as_posix()}/ after the render")
    eye_verdict.require(ctx.home / TAKES, takes, "EYE", ASK, home=ctx.home)


if __name__ == "__main__":
    raise SystemExit(step_cli.main(sys.modules[__name__], sys.argv))
