#!/usr/bin/env python
"""Check a finished trailer against the things that make trailers look cheap.

Every check here is mechanical and every one can fail.  That is the point: the
first trailer was judged by watching it, and watching it produced two wrong
diagnoses from me before the job files gave the right one.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio.beatmap import envelope
from studio.trailer_cut import is_uniform

ROOT = Path(__file__).resolve().parents[2]


def loudness(video: Path) -> tuple[float, float]:
    """(integrated LUFS, true peak dBTP) of the finished file."""
    result = subprocess.run(
        ["ffmpeg", "-i", str(video), "-af", "loudnorm=print_format=json",
         "-f", "null", "-"], capture_output=True, text=True, errors="replace")
    tail = result.stderr[result.stderr.rfind("{"):result.stderr.rfind("}") + 1]
    try:
        report = json.loads(tail)
        return float(report["input_i"]), float(report["input_tp"])
    except (ValueError, KeyError):
        return 0.0, 0.0


def scene_cuts(video: Path, threshold: float = 0.35) -> int:
    """How many hard cuts the finished picture actually contains."""
    result = subprocess.run(
        ["ffmpeg", "-i", str(video), "-vf", f"select='gt(scene,{threshold})',showinfo",
         "-f", "null", "-"], capture_output=True, text=True, errors="replace")
    return result.stderr.count("pts_time:")


def check(book_glob: str, trailer_id: str = "main") -> list[tuple[bool, str]]:
    book = next(p for p in (ROOT / "library").iterdir() if p.name.startswith(book_glob))
    out = book / "trailer" / trailer_id
    plan = json.loads((out / "plan.json").read_text(encoding="utf-8"))
    video = next(out.glob("TRAILER-*.mp4"))
    lengths = [s["seconds"] for s in plan["shots"]]
    integrated, peak = loudness(video)
    times, db = envelope(video)
    results = [
        (not is_uniform(lengths),
         f"shot lengths vary ({min(lengths):.2f}s to {max(lengths):.2f}s)"),
        (not plan_unbound(plan), "every shot carries its characters' references"),
        (peak <= -0.9, f"true peak {peak:.2f} dBTP (EBU R128 wants <= -1.0)"),
        (-16.0 <= integrated <= -12.5, f"integrated {integrated:.1f} LUFS (target -14)"),
        (max(lengths) / min(lengths) >= 2.0,
         f"longest shot is {max(lengths) / min(lengths):.1f}x the shortest"),
        (float(db.max() - db.min()) >= 20.0,
         f"dynamic range {float(db.max() - db.min()):.1f} dB (a flat mix reads cheap)"),
        (len(lengths) >= 12, f"{len(lengths)} shots"),
    ]
    return results


def plan_unbound(plan: dict) -> list:
    return [s for s in plan["shots"]
            if any(c not in s["char_refs"] for c in s["cast"])]


if __name__ == "__main__":
    failures = 0
    for passed, note in check(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "main"):
        print(f"  {'PASS' if passed else 'FAIL'}  {note}")
        failures += not passed
    print(f"{'all checks pass' if not failures else f'{failures} FAILING'}")
    sys.exit(1 if failures else 0)
