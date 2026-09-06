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

With a cue plan on disk the step settles the way an editor does (row 53):
the cue bends, the story does not.  A lost accent is absorbed by the shot
before it; a lost phrase, sustain or trough is cut OUT of the music and
everything after moves up; a lost button moves the hard out.  Only then
does step 06's spans path lay the survivors, with nothing left to fold, so
every take keeps the length it was rendered at.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from scripts.trailer.assemble import build_at
from studio import cue_edit, cue_settle
from studio.clip_cache import fresh
from studio.cue_plan import CuePlan
from studio.learnings import Learning
from studio.trailer_stage_spec import Metre

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


def cue_plan_of(ctx) -> CuePlan | None:
    """Step 03's measured spans when it wrote them; None is the walk."""
    path = ctx.out_dir / "music/plan.json"
    if not path.exists():
        return None
    return CuePlan.model_validate_json(path.read_text(encoding="utf-8"))


def cut_map_name(rel_path: str) -> str:
    """The cut map beside a cue: `cue-1003.flac` -> `cutmap-1003.json`, and
    the settled cue's beside it, so qc grades against the cue that plays."""
    return f"cutmap-{Path(rel_path).stem.removeprefix('cue-')}.json"


def settled_rel(cue: CuePlan) -> str:
    """The settled cue's path beside the original, one file however many
    passes settle it."""
    seed = Path(cue.rel_path).stem.removeprefix("cue-").removesuffix("-settled")
    return (Path(cue.rel_path).parent / f"cue-{seed}-settled.flac").as_posix()


def read_cue(path: Path) -> tuple[np.ndarray, int]:
    import soundfile
    samples, rate = soundfile.read(path, dtype="float32")
    return samples, int(rate)


def write_cue(path: Path, samples: np.ndarray, rate: int) -> None:
    import soundfile
    soundfile.write(path, samples, rate, subtype="PCM_16")


def cut_cue(ctx, cue: CuePlan, removed: list[tuple[float, float]]) -> str:
    """Every removed range spliced out of the cue in order, the metre and the
    cut map moved with it; the settled cue's rel_path."""
    music = ctx.out_dir / "music"
    metre = Metre.model_validate_json((music / "metre.json").read_text(encoding="utf-8"))
    cut_map = json.loads((music / cut_map_name(cue.rel_path)).read_text(encoding="utf-8"))
    samples, rate = read_cue(ctx.book_dir / cue.rel_path)
    for start, end in removed:
        samples, recut = cue_edit.remove_range(samples, rate, metre, start, end)
        metre, cut_map = recut.metre, cue_settle.shifted_cut_map(cut_map, start, end)
    rel = settled_rel(cue)
    write_cue(ctx.book_dir / rel, samples, rate)
    (music / "metre.json").write_text(metre.model_copy(update={"rel_path": rel})
                                      .model_dump_json(indent=2, by_alias=True), encoding="utf-8")
    (music / cut_map_name(rel)).write_text(json.dumps(cut_map, indent=2), encoding="utf-8")
    return rel


def fold_instead(ctx, attempt: int, keep: list[str], exc: Exception) -> None:
    """The cue refused a join: the music stays whole, the spans fold to the
    survivors, and the run learns why."""
    ctx.learn(Learning(step=STEP_ID, gate="settle", measured=str(exc)[:80], action="folded",
                       attempt=attempt + 1, note="the cue kept its length; spans folded"))
    refit(ctx, attempt, rendered=keep)


def settled(ctx, attempt: int, keep: list[str]) -> None:
    """Re-plan around the takes that exist.  With a cue plan the cue is
    settled first and the survivors laid over it; without one, the walk."""
    cue = cue_plan_of(ctx)
    if cue is None:
        return refit(ctx, attempt, rendered=keep)
    out = cue_settle.settle(cue, [s["beat_id"] for s in plan_of(ctx)["shots"]], set(keep))
    try:
        rel = cut_cue(ctx, cue, out.removed) if out.removed else cue.rel_path
    except ValueError as exc:
        return fold_instead(ctx, attempt, keep, exc)
    plan = out.plan.model_copy(update={"rel_path": rel})
    (ctx.out_dir / "music/plan.json").write_text(plan.model_dump_json(indent=2), encoding="utf-8")
    print(f"[{STEP_ID}] settled: {len(out.removed)} range(s) cut from the cue, "
          f"{plan.seconds:.1f}s left, {len(out.ids)} spans filled")
    refit(ctx, attempt, rendered=out.ids)


def master_of(ctx) -> Path:
    found = sorted(ctx.out_dir.glob("TRAILER-*.mp4"))
    if not found:
        raise RuntimeError(f"no master under {ctx.out_dir}")
    return found[-1]


def recut(ctx, attempt: int) -> Path:
    """Re-plan around the takes that exist, at a longer stretch, then cut; free."""
    settled(ctx, attempt, usable(clips_of(ctx), plan_of(ctx), ctx.book_dir))
    settle(ctx, attempt)
    return build_at(ctx.book_dir, ctx.trailer_id)


SETTLE_PASSES = 3
"""Re-fits the walk may take before the cut is refused as unsettled."""


def settle(ctx, attempt: int = 0, passes: int = SETTLE_PASSES) -> list[str]:
    """Settle until every planned beat is usable at the length the plan gave it.

    On the walk, fewer takes make each shot longer, so a capped take that
    held its shot may outrun its cap after the re-fit; one pass is not a
    fixed point.  On the spans path every take keeps its length and the
    first pass is the last.
    """
    for _ in range(passes):
        clips = clips_of(ctx)
        keep = usable(clips, plan_of(ctx), ctx.book_dir)
        if keep == [shot["beat_id"] for shot in plan_of(ctx)["shots"]]:
            return keep
        print(f"[{STEP_ID}] {len(keep)} takes usable; settling the plan on them")
        settled(ctx, attempt, keep)
    raise SystemExit(f"REFUSED: the walk did not settle on usable takes in "
                     f"{passes} passes")


def run(codex_id: str, ctx) -> None:
    settle(ctx)
    master = build_at(ctx.book_dir, ctx.trailer_id)
    if not master.exists():
        raise RuntimeError(f"no master written at {master}")
    print(f"[{STEP_ID}] {master_of(ctx).name}")
