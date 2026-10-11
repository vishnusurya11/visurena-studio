#!/usr/bin/env python
"""Step 05 -- timeline: every shot's seconds from the measured voice.

    uv run python scripts/episode/step_05_timeline.py <codex_id> <n>

Wraps scripts/episode/respot.py then scripts/episode/timeline.py.  Done when
the timeline on disk is the timeline of THIS plan and THIS voice
(episode_home.load_placed, the one door, refuses a missing or stale one).
Free, no GPU.

A measured hole in speech over the wall gets ONE bounded auto-trim
(`autotrim`): holds of the shots inside the measured hole shaved to the
margin wall, one respot+timeline re-run, the free battery, and the PLAN
JUDGE's re-sign -- the no-human-input path.  Rendered takes refuse
untrimmed; a still-refused re-run or a refused battery is a SystemExit back
to step 02.  RISK, accepted: a crash between write_plan and the re-sign
leaves an unsigned plan with a fresh placed.json; drive then re-enters step
02, whose grandfathered logic sees the STALE verdict file and re-judges via
the ladder -- correct, at the cost of one critic call.
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
    if not (fresh(ctx.book_dir, ctx.number) and speech_gap.refusal(placed_of(ctx.book_dir, ctx.number)) is None):
        return False
    return rendered(ctx) or not packed(ctx)     # ep26: a fresh timeline packing a pair is not done


def rendered(ctx) -> bool:
    """Takes on disk: the step_02 guard, applied to the trim -- a plan whose
    takes were rendered is never edited (ep13, 2026-09-27)."""
    home = episode_home.home(ctx.book_dir, ctx.number)
    return any((home / "takes" / "r2v").glob("T??.mp4"))


def retime(ctx) -> None:
    """respot then timeline: the step's own body, re-usable for the one re-run."""
    ctx.run_script("scripts/episode/respot.py", clock="respot")
    ctx.run_script("scripts/episode/timeline.py", clock="timeline")


def judge_signer() -> str:
    """The plan judge's identity (`plan_ladder.Desk.sign` signs with the same):
    the no-human-input path signs in the judge's name, never the owner's."""
    from studio.judges import plan as plan_judge
    from studio.judges.verdict import signer
    return signer(plan_judge.JUDGE, plan_judge.VERSION)


def trimmed(ctx, placed: dict) -> int:
    """The bounded measured-hole trim, written through the contract (which
    lapses plan.verdict.json by sha8); 0 = nothing trimmable."""
    from studio import plan_cures
    path = episode_home.home(ctx.book_dir, ctx.number) / "plan.json"
    if not path.exists():
        return 0                       # nothing to trim: the original refusal stands
    doc = episode_home.read_json(path)
    n = plan_cures.trim_measured_holes(doc, placed)
    if n:
        from studio import plan_provenance, plan_verdict
        before = plan_verdict.plan_sha8(path)
        episode_home.write_plan(path, doc)
        # RECORDED: a trim that the re-run then refuses leaves the signature lapsed
        # by one link; step 02's resigned() carries it over a recorded chain, and
        # without the record it re-planned ep21 over its voices and timeline
        # (2026-10-08 07:40Z, a 31-shot signed plan lost to a fresh draft)
        plan_provenance.record(path, before, ["trim_measured_holes"])
    return n


def resign(ctx, n: int, why: str = "measured-hole trim") -> None:
    """The free battery, then the plan judge's signature; a refusal is a
    SystemExit back to step 02, where the judge ladder re-signs."""
    from studio import plan_verdict
    rc, out = ctx.capture_script("scripts/episode/plan_check.py")
    if rc:
        rows = "\n".join(l for l in out.splitlines() if l.strip())
        raise SystemExit(f"REFUSED: the {why} left battery faults:\n{rows[-1500:]}")
    what = f"{n} holds shaved" if why == "measured-hole trim" else f"{n} pair(s) unpacked"
    plan_verdict.sign(episode_home.home(ctx.book_dir, ctx.number) / "plan.json",
                      note=f"step 05 {why} ({what}); battery clean",
                      signed_by=judge_signer())


def packed(ctx) -> list[list[int]]:
    """Runs of shots the take packer puts in ONE take on the MEASURED timeline."""
    from studio import episode_takes as tk
    plan = episode_home.read_json(episode_home.home(ctx.book_dir, ctx.number) / "plan.json")
    setups = {s["index"]: s.get("setup") for s in plan.get("shots") or []}
    rows = [dict(s, setup=setups.get(s["index"])) for s in placed_of(ctx.book_dir, ctx.number).get("shots") or []]
    return [g for g in tk.groups(rows) if len(g) > 1]


def unpacked(ctx) -> int:
    """The hold cure by the RECORDED voice, written and recorded; 0 = no change."""
    from studio import plan_cures, plan_gates, plan_provenance, plan_verdict
    path = episode_home.home(ctx.book_dir, ctx.number) / "plan.json"
    doc = episode_home.read_json(path)
    plan_gates.use_voice(ctx.book_dir, ctx.number)
    cured = plan_cures.holds(episode_home.read_json(path), rate=plan_gates.series_rate(ctx.book_dir, ctx.number))
    if cured == doc:
        return 0
    before = plan_verdict.plan_sha8(path)
    episode_home.write_plan(path, cured)
    plan_provenance.record(path, before, ["holds"])
    return 1


def unpack(ctx) -> None:
    """ep26 (2026-10-09): a pair clean at the RATE packed under the voice and
    step 06 refused the take.  Unpack it here, re-time, re-sign -- once."""
    if rendered(ctx) or not (pairs := packed(ctx)):
        return
    if not unpacked(ctx):
        raise SystemExit(f"REFUSED: the measured timeline packs {pairs} into one take and the hold cure moves nothing")
    retime(ctx)
    if again := packed(ctx):
        raise SystemExit(f"REFUSED: the measured timeline still packs {again} after the hold cure")
    # the hold cure may split a shot (two equal moves running, ep26 11:45Z): the
    # free repair rounds -- recorded cures, no writer -- then the timeline again
    ctx.capture_script("scripts/episode/plan_repair.py", "--no-llm")
    retime(ctx)
    resign(ctx, len(pairs), why="measured-pair unpack")


def autotrim(ctx, why: str) -> None:
    """The decision: rendered -> refuse untrimmed; untrimmable -> refuse with
    the original text; else ONE trim, ONE re-run, re-check, battery, re-sign."""
    if rendered(ctx):
        raise SystemExit(why)
    if not (n := trimmed(ctx, placed_of(ctx.book_dir, ctx.number))):
        raise SystemExit(why)
    retime(ctx)
    if again := speech_gap.refusal(placed_of(ctx.book_dir, ctx.number)):
        raise SystemExit(again)
    resign(ctx, n)


def run(ctx) -> None:
    retime(ctx)
    if why := speech_gap.refusal(placed_of(ctx.book_dir, ctx.number)):
        autotrim(ctx, why)
    unpack(ctx)


if __name__ == "__main__":
    raise SystemExit(step_cli.main(sys.modules[__name__], sys.argv))
