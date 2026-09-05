"""Step 08 -- assemble: the deterministic cut.

No gate of its own: `assemble.build_at` measures the picture it makes and
refuses drift, and an exception here is a bug to fix, not a rung to climb.
What the step adds is step 07's verdicts.  A take that never rendered, one
capped shorter than its shot, and a file left behind by an earlier plan are
all the same thing to the cut: a beat with no picture of its own.  None of
them buys a stand-in any more -- the plan is re-fitted around the takes that
exist and the trailer gets shorter, because the owner's rule is that a
rendered take is never seen twice.  `recut` is the free re-cut step 09
climbs when the delivered master misses its targets.
"""
from __future__ import annotations

import json
from pathlib import Path

from scripts.trailer.assemble import build_at
from studio.clip_cache import fresh

STEP_ID = "08"
NAME = "assemble"


def usable(clips: dict, plan: dict, book: Path) -> list[str]:
    """The beats this cut may play: fresh on disk, and long enough for the shot.

    A capped take is one whose face never bound; step 07 rules it good only
    for a cut under its cap, and with no neighbour left to borrow from, a
    beat whose shot outruns that cap leaves the plan.
    """
    capped = {c["beat_id"]: c["capped"] for c in clips["clips"] if c.get("capped")}
    seconds = {s["beat_id"]: s["seconds"] for s in plan["shots"]}
    have = set(fresh(clips, book))
    return [b for b in (s["beat_id"] for s in plan["shots"])
            if b in have and seconds[b] <= capped.get(b, seconds[b])]


def clips_of(ctx) -> dict:
    """Step 07's record of what it promoted; the cut may not guess without it."""
    path = ctx.out_dir / "clips.json"
    if not path.exists():
        raise SystemExit(f"REFUSED: no clips.json under {ctx.out_dir}; nothing "
                         f"says which takes this plan rendered")
    return json.loads(path.read_text(encoding="utf-8"))


def plan_of(ctx) -> dict:
    return json.loads((ctx.out_dir / "plan.json").read_text(encoding="utf-8"))


def refit(ctx, attempt: int, rendered: list[str]) -> None:
    """Step 06 owns the walk; imported here so step 08 loads without it."""
    from scripts.trailer import step_06_plan
    step_06_plan.refit(ctx, attempt, rendered=rendered)


def master_of(ctx) -> Path:
    found = sorted(ctx.out_dir.glob("TRAILER-*.mp4"))
    if not found:
        raise RuntimeError(f"no master under {ctx.out_dir}")
    return found[-1]


def recut(ctx, attempt: int) -> Path:
    """Re-plan around the takes that exist, at a longer stretch, then cut; free."""
    refit(ctx, attempt, rendered=usable(clips_of(ctx), plan_of(ctx), ctx.book_dir))
    return build_at(ctx.book_dir, ctx.trailer_id)


def run(codex_id: str, ctx) -> None:
    keep = usable(clips_of(ctx), plan_of(ctx), ctx.book_dir)
    if keep != [shot["beat_id"] for shot in plan_of(ctx)["shots"]]:
        print(f"[{STEP_ID}] {len(keep)} takes usable; re-fitting the walk to them")
        refit(ctx, 0, rendered=keep)
    master = build_at(ctx.book_dir, ctx.trailer_id)
    if not master.exists():
        raise RuntimeError(f"no master written at {master}")
    print(f"[{STEP_ID}] {master_of(ctx).name}")
