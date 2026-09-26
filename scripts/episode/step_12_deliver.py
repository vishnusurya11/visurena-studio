#!/usr/bin/env python
"""Step 12 -- deliver: the manifest beside the master, and the master's path first.

    uv run python scripts/episode/step_12_deliver.py <codex_id> <n>

episodes/epNN/manifest.json: the master (relative to the library), the QC
summary, every step's latest event (db.unit_status) and the wall time the
clock stamped (studio/episode_clock) -- and beside them the department
contract, studio/manifest.UnitManifest: the registry's declared inputs and
outputs matched on disk with their sha8, every verdict with its signer, the
cost.  The deliverable is the pair whose QC passed
(studio/youtube_publish.deliverable).  Never publishes, never sends: the
manifest is written and the master's absolute path is printed on its own
line first.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import db, episode_clock, episode_home, manifest as unit_manifest, step_cli  # noqa: E402
from studio import youtube_publish as yp  # noqa: E402

STEP_ID = "12"
NAME = "deliver"
GPU = False
QC_KEYS = ("passed", "sha8", "seconds", "planned_seconds", "lufs", "true_peak",
           "longest_gap_s", "missing_cuts", "takes")


def summary(report: dict) -> dict:
    """The QC numbers a reader wants, never the whole report."""
    return {key: report.get(key) for key in QC_KEYS}


def timing(book: Path, number: int) -> dict:
    """Total seconds and per-stage sums off timing.jsonl; retries counted."""
    rows = episode_clock.rows(book, number)
    by_stage: dict[str, float] = {}
    for row in rows:
        by_stage[row["stage"]] = round(by_stage.get(row["stage"], 0.0) + row["seconds"], 1)
    return {"total_seconds": round(sum(r["seconds"] for r in rows), 1), "runs": len(rows),
            "by_stage": by_stage}


def library_relative(path: Path) -> str:
    """How the manifest names the master: relative to the library, posix."""
    return Path(path).resolve().relative_to(episode_home.LIBRARY.resolve()).as_posix()


def manifest(ctx, master: Path, report: dict) -> dict:
    return {"codex_id": ctx.codex_id, "unit": ctx.unit, "number": ctx.number,
            "master": library_relative(master), "qc": summary(report),
            "steps": db.unit_status(ctx.conn, ctx.codex_id, ctx.stage, ctx.unit),
            "timing": timing(ctx.book_dir, ctx.number)}


def done(ctx) -> bool:
    out = ctx.home / "manifest.json"
    try:
        _engine, _master, qc = yp.deliverable(ctx.home, "")
    except SystemExit:
        return False
    if not out.exists():
        return False
    return episode_home.read_json(out).get("qc", {}).get("sha8") == episode_home.read_json(qc).get("sha8")


def write(ctx, master: Path, report: dict) -> Path:
    """The contract's manifest at the unit's home, this step's own keys beside it."""
    contract = unit_manifest.manifest_for(ctx, ctx.stage)
    return unit_manifest.write_manifest(ctx.book_dir, unit_manifest.home_of(ctx.stage, ctx.unit),
                                        contract, extra=manifest(ctx, master, report))


def run(ctx) -> None:
    _engine, master, qc = yp.deliverable(ctx.home, "")
    out = write(ctx, master, episode_home.read_json(qc))
    print(str(master.resolve()))
    print(f"manifest -> {out}")


if __name__ == "__main__":
    raise SystemExit(step_cli.main(sys.modules[__name__], sys.argv))
