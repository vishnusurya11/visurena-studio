"""Step 08 -- assemble: the deterministic cut.

No gate of its own: `assemble.build_at` measures the picture it makes and
refuses drift, and an exception here is a bug to fix, not a rung to climb.
What the step adds is step 07's verdicts.  A take capped short serves only
the shots under its cap; a dropped beat has no file; both are sourced from
a neighbouring take exactly as a missing render always was.  `recut` is
the free re-cut step 09 climbs when the delivered master misses its targets.
"""
from __future__ import annotations

import json
from pathlib import Path

from scripts.trailer.assemble import Resolver, build_at, neighbouring_take

STEP_ID = "08"
NAME = "assemble"


def resolver_for(clips: dict | None) -> Resolver:
    """Which take each shot reads, given what step 07 measured."""
    if clips is None:
        return neighbouring_take
    capped = {c["beat_id"]: c["capped"] for c in clips["clips"] if c.get("capped")}

    def resolve(beat_id: str, order: int, seconds: float, have: list[str]) -> str:
        if beat_id in capped and seconds > capped[beat_id]:
            return neighbouring_take(f"{beat_id}:capped", order, seconds, have)
        return neighbouring_take(beat_id, order, seconds, have)
    return resolve


def clips_of(ctx) -> dict | None:
    path = ctx.out_dir / "clips.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def master_of(ctx) -> Path:
    found = sorted(ctx.out_dir.glob("TRAILER-*.mp4"))
    if not found:
        raise RuntimeError(f"no master under {ctx.out_dir}")
    return found[-1]


def recut(ctx, attempt: int) -> Path:
    """Re-plan the cuts with the walk stretched, then cut again; free."""
    from scripts.trailer import step_06_plan  # step 06 owns the walk
    step_06_plan.replan(ctx, attempt)
    return build_at(ctx.book_dir, ctx.trailer_id, resolver_for(clips_of(ctx)))


def run(codex_id: str, ctx) -> None:
    master = build_at(ctx.book_dir, ctx.trailer_id, resolver_for(clips_of(ctx)))
    if not master.exists():
        raise RuntimeError(f"no master written at {master}")
    print(f"[{STEP_ID}] {master_of(ctx).name}")
