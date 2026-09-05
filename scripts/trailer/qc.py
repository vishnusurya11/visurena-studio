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

from studio import beatmap, clip_cache, trailer_assemble
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


def line_over_bed(out_dir: Path, momentary: Callable = trailer_assemble.momentary,
                  integrated: Callable = trailer_assemble.integrated,
                  seconds: Callable = trailer_assemble.clip_seconds) -> list[float]:
    """LU each line rides over the ducked bed under its own window, from
    what the mix left beside the master: `lines.level.json` (where each
    levelled line was laid), `line-N.level.wav`, and `<master>.bed-ducked.wav`.
    A master mixed without lines has no sheet and measures nothing."""
    sheet = out_dir / "lines.level.json"
    ducked = out_dir / f"{master_of(out_dir).stem}.bed-ducked.wav"
    if not sheet.exists() or not ducked.exists():
        return []
    readings = momentary(ducked)
    out = []
    for row in json.loads(sheet.read_text(encoding="utf-8")):
        line = out_dir / row["rel_path"]
        at = float(row["at"])
        bed = trailer_assemble.bed_level(readings, at, at + seconds(line))
        out.append(round(integrated(line) - bed, 2))
    return out


def on_music(found: Metre) -> list[float]:
    """Every point a cut can land on: the beats and the L0 events, which the
    walk cuts on and the tracker places between beats (run 10: 8 of 13
    'off-beat' cuts sat on stopdowns and hits)."""
    return sorted(set(found.beats) | set(level_zero(found)))


def graded(cuts: list[float], found: Metre, tol: float = ON_GRID) -> list[float]:
    """The cuts inside the span the grid covers: before the first beat and
    after the last there is no pulse to be on or off."""
    if not found.beats:
        return []
    return [c for c in cuts if found.beats[0] - tol <= c <= found.beats[-1] + tol]


def reused_shots(shots: list[dict]) -> int:
    """Shots playing a take an earlier shot already played.

    A shot with no beat_id cannot be shown to repeat anything, so it counts
    as its own picture rather than as a nameless duplicate.
    """
    ids = [shot.get("beat_id", index) for index, shot in enumerate(shots)]
    return len(ids) - len(set(ids))


def stale_shots(shots: list[dict], fresh: list[str] | None) -> int:
    """Shots cut from a clip that is not this plan's own render.  Without a
    freshness reading nothing is claimed: the number is 0, not a guess."""
    if fresh is None:
        return 0
    return sum(1 for shot in shots if shot.get("beat_id") not in set(fresh))


def fresh_shots(out_dir: Path) -> list[str]:
    """The beats whose clip on disk is the take step 07 promoted this run.
    A trailer with no clips.json has none, so every shot reads as stale."""
    path = out_dir / "clips.json"
    if not path.exists():
        return []
    doc = json.loads(path.read_text(encoding="utf-8"))
    return clip_cache.fresh(doc, out_dir.parents[1])


def report(plan: dict, found: Metre, seen: list[float], loud: tuple[float, float],
           lines_lu: list[float] = (), fresh: list[str] | None = None) -> QCReport:
    """The QCReport from the measured grid, the detected cuts, the loudness,
    each line's LU over the ducked bed (`line_over_bed`), and whether any
    picture in the cut is one the viewer has already seen."""
    lengths = [float(s["seconds"]) for s in plan["shots"]]
    title_at = planned_cuts(plan)[-1]
    inside = graded(seen, found)
    return QCReport(
        cuts=len(seen), cuts_on_beat=fraction_on(inside, on_music(found)),
        cuts_on_downbeat=fraction_on(inside, sorted(set(found.downbeats) | set(level_zero(found)))),
        cuts_on_L0=fraction_on(level_zero(found), seen),
        on_cap_fraction=on_cap_fraction(lengths, max_shot(found.bar)),
        title_on_downbeat=any(abs(title_at - d) <= ON_GRID for d in found.downbeats),
        integrated_lufs=loud[0], true_peak=loud[1], unbound_shots=len(plan_unbound(plan)),
        reused_shots=reused_shots(plan["shots"]),
        stale_shots=stale_shots(plan["shots"], fresh),
        line_over_bed_lu=list(lines_lu), grid=found.grid)


def master_of(out_dir: Path) -> Path:
    return next(out_dir.glob("TRAILER-*.mp4"))


def qc(out_dir: Path, detect: Callable = scene_cuts, track: beatmap.Tracker | None = None,
       measure: Callable = beatmap.metre, loud: Callable = loudness,
       threshold: float = SCENE_THRESHOLD, lines: Callable = line_over_bed,
       fresh: Callable = fresh_shots) -> QCReport:
    """Measure the master in `out_dir`, write qc.json beside it, return the report.

    The master's own audio is what the tracker reads -- `beatmap.decode`
    takes any container ffmpeg can open, so no separate extraction step.
    """
    video = master_of(out_dir)
    plan = json.loads((out_dir / "plan.json").read_text(encoding="utf-8"))
    seen = detect(video, threshold=threshold)
    found = measure(video, seed=0, rel_path=video.name, track=track)
    result = report(plan, found, seen, loud(video), lines(out_dir), fresh(out_dir))
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
