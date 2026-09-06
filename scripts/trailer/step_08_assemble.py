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

The step settles the way an editor does (row 53): the cue bends, the story
does not.  A lost accent is absorbed by the shot before it; a lost phrase,
sustain or trough is cut OUT of the music and everything after moves up; a
lost button moves the hard out.  Only then does step 06 lay the survivors on
the settled spans, with nothing left to fold, so every take keeps the length
it was rendered at.  Step 03's cue plan is the one thing every re-fit reads;
without it the step refuses (row 55), because nothing here may invent a cut.
"""
from __future__ import annotations

import json
from pathlib import Path

from scripts.trailer.assemble import build_at
from studio import cue_conform, cue_settle
from studio.clip_cache import fresh
from studio.cue_plan import CuePlan
from studio.learnings import Learning

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


def refit(ctx, rendered: list[str]) -> None:
    """Step 06 owns the plan; imported here so step 08 loads without it."""
    from scripts.trailer import step_06_plan
    step_06_plan.refit(ctx, rendered=rendered)


def cue_plan_of(ctx) -> CuePlan:
    """Step 03's measured spans; their absence is a refusal, not a fallback."""
    path = ctx.out_dir / "music/plan.json"
    if not path.exists():
        raise FileNotFoundError(f"[{STEP_ID}] music/plan.json is missing: the cut settles on "
                                f"step 03's spans and has no other cut to make")
    return CuePlan.model_validate_json(path.read_text(encoding="utf-8"))


def cut_cue(ctx, cue: CuePlan, removed: list[tuple[float, float]]) -> str:
    """Every removed range cut out of the cue in order, the metre and the cut
    map moved with it (`cue_conform.cut_files`); the settled cue's rel_path."""
    return cue_conform.cut_files(ctx.out_dir / "music", ctx.book_dir, cue, removed)


def fold_instead(ctx, attempt: int, keep: list[str], exc: Exception) -> None:
    """The cue refused a join: the music stays whole, the spans fold to the
    survivors, and the run learns why."""
    ctx.learn(Learning(step=STEP_ID, gate="settle", measured=str(exc)[:80], action="folded",
                       attempt=attempt + 1, note="the cue kept its length; spans folded"))
    refit(ctx, rendered=keep)


def settled(ctx, attempt: int, keep: list[str]) -> None:
    """Re-plan around the takes that exist: the cue is settled first and the
    survivors laid over it."""
    cue = cue_plan_of(ctx)
    out = cue_settle.settle(cue, [s["beat_id"] for s in plan_of(ctx)["shots"]], set(keep))
    try:
        rel = cut_cue(ctx, cue, out.removed) if out.removed else cue.rel_path
    except ValueError as exc:
        return fold_instead(ctx, attempt, keep, exc)
    plan = out.plan.model_copy(update={"rel_path": rel})
    (ctx.out_dir / "music/plan.json").write_text(plan.model_dump_json(indent=2), encoding="utf-8")
    print(f"[{STEP_ID}] settled: {len(out.removed)} range(s) cut from the cue, "
          f"{plan.seconds:.1f}s left, {len(out.ids)} spans filled")
    refit(ctx, rendered=out.ids)


def master_of(ctx) -> Path:
    found = sorted(ctx.out_dir.glob("TRAILER-*.mp4"))
    if not found:
        raise RuntimeError(f"no master under {ctx.out_dir}")
    return found[-1]


def recut(ctx, attempt: int) -> Path:
    """Re-plan around the takes that exist, then cut; free.  `attempt` is
    step 09's rung, recorded with what the settle learns."""
    settled(ctx, attempt, usable(clips_of(ctx), plan_of(ctx), ctx.book_dir))
    settle(ctx, attempt)
    return build_at(ctx.book_dir, ctx.trailer_id)


SETTLE_PASSES = 3
"""Re-fits the plan may take before the cut is refused as unsettled."""


def settle(ctx, attempt: int = 0, passes: int = SETTLE_PASSES) -> list[str]:
    """Settle until every planned beat is usable at the length the plan gave it.

    On the spans every take keeps its length, so the first pass is the last;
    the loop is the guard that says so on disk if a re-fit ever changes a
    length again.
    """
    for _ in range(passes):
        clips = clips_of(ctx)
        keep = usable(clips, plan_of(ctx), ctx.book_dir)
        if keep == [shot["beat_id"] for shot in plan_of(ctx)["shots"]]:
            return keep
        print(f"[{STEP_ID}] {len(keep)} takes usable; settling the plan on them")
        settled(ctx, attempt, keep)
    raise SystemExit(f"REFUSED: the plan did not settle on usable takes in "
                     f"{passes} passes")


def run(codex_id: str, ctx) -> None:
    settle(ctx)
    master = build_at(ctx.book_dir, ctx.trailer_id)
    if not master.exists():
        raise RuntimeError(f"no master written at {master}")
    print(f"[{STEP_ID}] {master_of(ctx).name}")
