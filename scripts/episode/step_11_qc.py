#!/usr/bin/env python
"""Step 11 -- qc: measure the delivered master, then the owner watches it.

    uv run python scripts/episode/step_11_qc.py <codex_id> <n> [--engine=r2v]

Wraps scripts/episode/qc.py --engine=r2v, which stamps the sha8 it measured
into the report beside the master (episodes/epNN/qc_<engine>.json, the pair
studio/youtube_publish.MASTERS names).  A FAIL is a refusal.  A PASS asks for
the master eye: review/eye_<sha8>.json, the rubric scripts/episode/eye_review.py
writes blank and a person fills; an unanswered or unwaived rubric is no verdict.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.episode import eye_review  # noqa: E402
from studio import episode_home, step_cli, youtube_publish as yp  # noqa: E402
from studio.escalate import Escalation  # noqa: E402

STEP_ID = "11"
NAME = "qc"
GPU = True
ENGINE = "r2v"
ASK = "watch the master and answer the rubric (scripts/episode/eye_review.py)"


def engine_of(extra: list[str]) -> str:
    """`--engine=` when typed, else the house engine."""
    return next((a.split("=", 1)[1] for a in extra if a.startswith("--engine=")), ENGINE)


def engine_flags(extra: list[str]) -> list[str]:
    return [f"--engine={engine_of(extra)}", *[a for a in extra if not a.startswith("--engine=")]]


def pair(home: Path, engine: str) -> tuple[Path, Path]:
    """(master, qc report) for one engine, where qc.py and the publish ladder agree they are."""
    for name, master, qc in yp.MASTERS:
        if name == engine:
            return Path(home) / "cut" / master, Path(home) / qc
    raise SystemExit(f"unknown engine {engine!r}; one of {[n for n, _m, _q in yp.MASTERS]}")


def rubric_signed(home: Path, sha8: str) -> bool:
    """Whether review/eye_<sha8>.json exists and clears eye_review's refusals."""
    path = eye_review.rubric_path(home, sha8)
    if not path.exists():
        return False
    return not eye_review.refusals(episode_home.read_json(path), sha8, path)


def done(ctx) -> bool:
    master, qc = pair(ctx.home, engine_of(getattr(ctx, "extra", None) or []))
    if not (master.exists() and qc.exists()):
        return False
    report = episode_home.read_json(qc)
    return (bool(report.get("passed")) and report.get("sha8") == yp.sha8(master)
            and rubric_signed(ctx.home, report["sha8"]))


def run(ctx) -> None:
    extra = getattr(ctx, "extra", None) or []
    ctx.run_script("scripts/episode/qc.py", *engine_flags(extra), gpu=GPU, clock="qc")
    _master, qc = pair(ctx.home, engine_of(extra))
    if not qc.exists():
        raise SystemExit(f"REFUSED: qc.py left no report at {qc.name}")
    report = episode_home.read_json(qc)
    if not report.get("passed"):
        raise SystemExit(f"REFUSED: qc FAIL in {qc.name}; fix the cut before anyone watches it")
    if not rubric_signed(ctx.home, report["sha8"]):
        raise Escalation("MASTER", f"review/eye_{report['sha8']}.json", ASK)


if __name__ == "__main__":
    raise SystemExit(step_cli.main(sys.modules[__name__], sys.argv))
