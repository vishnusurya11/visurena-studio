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
    return fresh(ctx.book_dir, ctx.number) and speech_gap.refusal(placed_of(ctx.book_dir, ctx.number)) is None


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
        episode_home.write_plan(path, doc)
    return n


def resign(ctx, n: int) -> None:
    """The free battery, then the plan judge's signature; a refusal is a
    SystemExit back to step 02, where the judge ladder re-signs."""
    from studio import plan_verdict
    rc, out = ctx.capture_script("scripts/episode/plan_check.py")
    if rc:
        rows = "\n".join(l for l in out.splitlines() if l.strip())
        raise SystemExit(f"REFUSED: the measured-hole trim left battery faults:\n{rows[-1500:]}")
    plan_verdict.sign(episode_home.home(ctx.book_dir, ctx.number) / "plan.json",
                      note=f"step 05 measured-hole trim ({n} holds shaved); battery clean",
                      signed_by=judge_signer())


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


if __name__ == "__main__":
    raise SystemExit(step_cli.main(sys.modules[__name__], sys.argv))
