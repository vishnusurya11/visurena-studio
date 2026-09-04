#!/usr/bin/env python
"""Read the DELIVERED master and say, in numbers, how it sits on the music.

    uv run python scripts/trailer/qc.py <codex_id> [trailer_id]

Every number here is measured from the file that ships: the picture's cuts
by scene-detect, the grid by the tracker on the master's own audio, the
loudness by loudnorm.  The plan is consulted only to say which of its cuts
the picture LACKS, because a planned cut that never rendered is exactly
the kind of miss watching the trailer does not catch.  Writes qc.json
beside the master.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Callable

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import beatmap
from studio.paths import book_dir
from studio.trailer_edit import max_shot
from studio.trailer_stage_spec import Metre, QCReport

ON_GRID = 0.04
"""A cut within a frame of a beat is on it; beyond that it is near it."""
MATCH = 0.05
"""How far a detected cut may sit from its planned one and still be it."""
PTS = re.compile(r"pts_time:\s*([0-9.]+)")


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


SCENE_THRESHOLD = 0.1
"""MEASURED on the delivered Scarlet master against its 45 planned cuts:
0.35 finds 23 (22 missing), 0.2 finds 44, 0.1 finds all 45 with nothing
extra, 0.05 double-counts 18.  A graded, dark, slow-moving picture cuts
between frames that differ far less than ffmpeg's textbook 0.3-0.4."""


def scene_cuts(video: Path, threshold: float = SCENE_THRESHOLD) -> list[float]:
    """Timestamps of the hard cuts the finished picture actually contains."""
    result = subprocess.run(
        ["ffmpeg", "-i", str(video), "-vf", f"select='gt(scene,{threshold})',showinfo",
         "-f", "null", "-"], capture_output=True, text=True, errors="replace")
    return [round(float(m), 3) for m in PTS.findall(result.stderr)]


def planned_cuts(plan: dict) -> list[float]:
    """Every cut the plan asked for: each shot start after the first, then the card."""
    shots = plan["shots"]
    starts = [round(float(s["start"]), 4) for s in shots[1:]]
    return starts + [round(sum(float(s["seconds"]) for s in shots), 4)]


def missing_cuts(planned: list[float], seen: list[float], tol: float = MATCH) -> list[float]:
    """Planned cuts with no detected cut within `tol`."""
    return [p for p in planned if not any(abs(p - s) <= tol for s in seen)]


def fraction_on(cuts: list[float], grid: list[float], tol: float = ON_GRID) -> float:
    """The share of `cuts` within `tol` of a grid point."""
    if not cuts:
        return 0.0
    return sum(any(abs(c - g) <= tol for g in grid) for c in cuts) / len(cuts)


def on_cap_fraction(lengths: list[float], cap: float, tol: float = ON_GRID) -> float:
    """The share of shots sitting at the ceiling -- the tell of a starved grid."""
    if not lengths:
        return 0.0
    return sum(1 for x in lengths if x >= cap - tol) / len(lengths)


def plan_unbound(plan: dict) -> list:
    return [s for s in plan["shots"]
            if any(c not in s.get("char_refs", {}) for c in s.get("cast", []))]


def level_zero(found: Metre) -> list[float]:
    """The L0 events: structural hits, stopdowns and the title hit."""
    events = set(found.hits) | set(found.stopdowns)
    if found.title_hit is not None:
        events.add(found.title_hit)
    return sorted(events)


def report(plan: dict, found: Metre, seen: list[float], loud: tuple[float, float]) -> QCReport:
    """The QCReport from the measured grid, the detected cuts and the loudness.

    `line_over_bed_lu` stays empty: the delivered master has no stems to
    separate a line from its bed, and Track C owns the line layer.
    """
    lengths = [float(s["seconds"]) for s in plan["shots"]]
    title_at = planned_cuts(plan)[-1]
    return QCReport(
        cuts=len(seen), cuts_on_beat=fraction_on(seen, found.beats),
        cuts_on_downbeat=fraction_on(seen, found.downbeats),
        cuts_on_L0=fraction_on(level_zero(found), seen),
        on_cap_fraction=on_cap_fraction(lengths, max_shot(found.bar)),
        title_on_downbeat=any(abs(title_at - d) <= ON_GRID for d in found.downbeats),
        integrated_lufs=loud[0], true_peak=loud[1], unbound_shots=len(plan_unbound(plan)),
        grid=found.grid)


def master_of(out_dir: Path) -> Path:
    return next(out_dir.glob("TRAILER-*.mp4"))


def qc(out_dir: Path, detect: Callable = scene_cuts, track: beatmap.Tracker | None = None,
       measure: Callable = beatmap.metre, loud: Callable = loudness,
       threshold: float = SCENE_THRESHOLD) -> QCReport:
    """Measure the master in `out_dir`, write qc.json beside it, return the report.

    The master's own audio is what the tracker reads -- `beatmap.decode`
    takes any container ffmpeg can open, so no separate extraction step.
    """
    video = master_of(out_dir)
    plan = json.loads((out_dir / "plan.json").read_text(encoding="utf-8"))
    seen = detect(video, threshold=threshold)
    found = measure(video, seed=0, rel_path=video.name, track=track)
    result = report(plan, found, seen, loud(video))
    sidecar = result.model_dump() | {"missing_cuts": missing_cuts(planned_cuts(plan), seen),
                                    "flags": result.flags, "floor_pass": result.floor_pass}
    (out_dir / "qc.json").write_text(json.dumps(sidecar, indent=2), encoding="utf-8")
    return result


def main(codex_id: str, trailer_id: str = "main") -> QCReport:
    out = book_dir(codex_id) / "trailer" / trailer_id
    result = qc(out)
    written = json.loads((out / "qc.json").read_text(encoding="utf-8"))
    for key, value in written.items():
        print(f"  {key}: {value}")
    print("floor pass" if result.floor_pass else "FLOOR FAIL", "| flags:", ", ".join(result.flags) or "none")
    return result


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "main")
