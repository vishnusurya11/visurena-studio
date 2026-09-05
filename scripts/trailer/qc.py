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
from studio.trailer_cut import title_moment
from studio.trailer_edit import act_cap
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


def act_caps_of(shots: list[dict], bar: float) -> list[float]:
    """Each shot's length as a share of ITS act's ceiling, so a two-bar act-1
    shot at 92 BPM reads as inside its cap and a 4 s act-3 shot reads as on it."""
    duration = sum(float(s["seconds"]) for s in shots)
    if not duration:
        return []
    return [float(s["seconds"]) / act_cap(float(s["start"]) / duration, bar) * bar
            for s in shots]


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


def level_sheet(out_dir: Path) -> dict:
    """What the mix wrote down about itself: where each line was laid, how
    deep the bed ducked under it, and where the bed was stopped.

    Two shapes are read.  The current one is a document; run 10's was a bare
    list of {at, rel_path}, and the run-10 master is the only before-and-after
    reference this pipeline has, so it stays readable.
    """
    path = out_dir / "lines.level.json"
    if not path.exists():
        return {"hard_out": None, "lines": []}
    sheet = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(sheet, list):
        return {"hard_out": None, "lines": sheet}
    return sheet


def sheet_windows(sheet: dict, seconds: Callable = trailer_assemble.clip_seconds,
                  out_dir: Path | None = None) -> list[tuple[float, float]]:
    """(start, end) of every line the mix laid, from the sheet's own numbers.

    Run 10's sheet recorded no duration, so a line's end has to be measured
    off the file it names -- which is why the sheet records it now.
    """
    windows = []
    for row in sheet["lines"]:
        length = row.get("seconds")
        if length is None:
            length = seconds((out_dir or Path(".")) / row["rel_path"])
        windows.append((float(row["at"]), float(row["at"]) + float(length)))
    return windows


def line_over_bed(out_dir: Path, momentary: Callable = trailer_assemble.momentary,
                  integrated: Callable = trailer_assemble.integrated,
                  seconds: Callable = trailer_assemble.clip_seconds) -> list[float]:
    """LU each line rides over the ducked bed under its own window, from
    what the mix left beside the master: `lines.level.json`, `line-N.level.wav`,
    and `<master>.bed-ducked.wav`.  A master mixed without lines measures
    nothing."""
    sheet = level_sheet(out_dir)
    ducked = out_dir / f"{master_of(out_dir).stem}.bed-ducked.wav"
    if not sheet["lines"] or not ducked.exists():
        return []
    readings = momentary(ducked)
    windows = sheet_windows(sheet, seconds, out_dir)
    return [round(integrated(out_dir / row["rel_path"])
                  - trailer_assemble.bed_level(readings, start, end), 2)
            for row, (start, end) in zip(sheet["lines"], windows)]


AUDIBLE_M = -40.0
"""Momentary loudness above which something is playing.  Below it the
programme is a noise floor, not a layer."""

SAMPLE_GAP = 0.15
"""ebur128 prints every 100 ms; two readings further apart than this are two
different stretches, not one."""


def _runs(times: list[float], gap: float = SAMPLE_GAP) -> list[tuple[float, float]]:
    """Contiguous groups of sampled times, as (first, last) spans."""
    spans: list[list[float]] = []
    for t in times:
        if spans and t - spans[-1][1] <= gap:
            spans[-1][1] = t
        else:
            spans.append([t, t])
    return [(round(a, 2), round(b, 2)) for a, b in spans]


def music_only_runs(readings: list[tuple[float, float]],
                    windows: list[tuple[float, float]], until: float,
                    floor: float = AUDIBLE_M) -> list[tuple[float, float]]:
    """Every stretch where something plays and nobody speaks (A).

    Run 10 had two of these at 27 s and 40 s, and 92% of the runtime in
    total.  The norm is a bed under speech for 40-50% of the time and one
    final montage of 10-15 s where the music is allowed to be alone.
    """
    return _runs([t for t, m in readings if t < until and m > floor
                  and not any(start <= t < end for start, end in windows)])


def music_only_fraction(runs: list[tuple[float, float]], until: float) -> float:
    """The share of the picture that is music with nothing over it."""
    return round(sum(end - start for start, end in runs) / until, 3) if until else 0.0


def longest_music_only(runs: list[tuple[float, float]]) -> float:
    """The longest such stretch that is NOT the final montage."""
    return round(max((end - start for start, end in runs[:-1]), default=0.0), 2)


def final_music_only(runs: list[tuple[float, float]]) -> float:
    """The last stretch before the title -- the montage the norm lets run on."""
    return round(runs[-1][1] - runs[-1][0], 2) if runs else 0.0


def speech_occupancy(windows: list[tuple[float, float]], until: float) -> float:
    """The share of the picture with a voice on it.  Run 10: 0.021."""
    if not until:
        return 0.0
    return round(sum(min(end, until) - start for start, end in windows
                     if start < until) / until, 3)


def speech_target(seconds: float) -> float:
    """How much speech THIS length of trailer has to carry.

    A: >= 3 lines per 30 s, and >= 0.30 occupancy.  Those two disagree on a
    short trailer -- three lines of the 1.5-4 s the norm gives them is about
    6.6 s, which is 0.22 of 30 s and cannot be 0.30 however they are placed.
    So 0.22 is the floor up to 30 s (three real lines, back to back nowhere),
    rising to the 0.30 the 90-150 s norm measures by 60 s.  A 25 s trailer is
    asked for 0.22 and run 10, at 105 s, would have been asked for 0.30.
    """
    if seconds <= 30.0:
        return 0.22
    return round(min(0.30, 0.22 + 0.08 * (seconds - 30.0) / 30.0), 3)


def peak_position(short: list[tuple[float, float]], until: float,
                  head: float = 3.0) -> float:
    """Where the loudest short-term window sits, as a fraction of the picture.

    C asks for 0.78-0.92.  Run 10 peaked at 0.53 -- its chorus -- and never
    got back there.  The first 3 s are dropped because ebur128's short-term
    window has not filled and reports about -120 until it has.  A plateau at
    the maximum is reported where it BEGINS: the end of a long loud stretch
    is not where the trailer got loud.
    """
    inside = [(t, level) for t, level in short if head <= t < until]
    if not inside or not until:
        return 0.0
    loudest = max(level for _, level in inside)
    return round(min(t for t, level in inside if level == loudest) / until, 3)


def act_bounds(seconds: float, acts: int = 3) -> list[tuple[float, float]]:
    """The equal parts of the PICTURE.  The card is not an act."""
    return [(seconds * i / acts, seconds * (i + 1) / acts) for i in range(acts)]


def act_over_act(readings: list[tuple[float, float]], bounds: list[tuple[float, float]],
                 later: int = 2, earlier: int = 1) -> float:
    """LU one act gains over another (editor 14: act 3 >= act 2 + 2 LU)."""
    heard = [(t, m) for t, m in readings if m > -70.0]
    return round(trailer_assemble.window_loudness(heard, *bounds[later])
                 - trailer_assemble.window_loudness(heard, *bounds[earlier]), 2)


def longest_under(readings: list[tuple[float, float]], start: float, end: float,
                  ceiling: float) -> float:
    """The longest unbroken stretch inside [start, end) quieter than `ceiling`."""
    runs = _runs([t for t, m in readings if start <= t < end and m <= ceiling])
    return round(max((b - a for a, b in runs), default=0.0), 2)


HARD_OUT_BEFORE = -18.0
HARD_OUT_AFTER = -35.0
SETTLE = 0.4
"""How long after a gate the momentary reading is clear of it.  ebur128
integrates 400 ms, so a 20 ms stop cannot be seen any closer than that."""


def hard_out_ok(readings: list[tuple[float, float]], at: float,
                window: float = 0.5) -> bool:
    """True when the bed was playing and then simply STOPPED (D).

    Run 10 faded over 3 s into digital silence, which measures as a cue
    ending rather than as a trailer stopping.
    """
    before = trailer_assemble.window_peak(readings, at - window, at)
    after = trailer_assemble.window_peak(readings, at + SETTLE, at + SETTLE + window)
    return before >= HARD_OUT_BEFORE and after <= HARD_OUT_AFTER


def title_hit_lu(readings: list[tuple[float, float]], at: float,
                 window: float = 0.5) -> float:
    """How loud the DELIVERED master is where the card is struck.

    D asks that the cue is still alive at the hit, and run 10's cue had faded
    to -46 LUFS there.  The master is measured rather than the cue, because
    the cue is now deliberately STOPPED and what lands on the card is the
    synthesised impact -- so what this catches is a hit that never reached
    the file, or landed past its end, which is the same silence for a viewer.
    """
    return round(trailer_assemble.window_peak(readings, at, at + window, default=-70.0), 2)


def bed_under_lines(readings: list[tuple[float, float]],
                    windows: list[tuple[float, float]],
                    settle: float = SETTLE) -> list[float]:
    """The LOUDEST the ducked bed gets under each line (B: <= -24 LUFS).

    A peak, not a mean: a mean says the bed was mostly out of the way, and
    run 10's bed was mostly out of the way of a line it opened over at
    -9 LUFS because the duck took 160 ms to arrive.

    Read from `settle` INTO the window rather than from its start.  ebur128
    integrates 400 ms, so a reading at the line's onset is mostly the bed
    from before the duck opened, and reports music that is no longer playing
    -- measured on the run-10 rebuild, the same duck reads 4.7 LU at the
    onset and 15.0 LU three readings later.  That the duck is already at full
    depth when the line starts is guaranteed by the envelope's arithmetic
    (`trailer_assemble.duck_db`) and verified on a rendered file in the line
    layer's tests; it cannot be seen at this resolution.
    """
    return [round(trailer_assemble.window_peak(readings, start + settle, end,
                                               default=-70.0), 2)
            for start, end in windows]


def on_beat_by_act(cuts: list[float], grid: list[float],
                   bounds: list[tuple[float, float]], tol: float = ON_GRID) -> list[float]:
    """The on-beat share of each act (G).

    One number for the whole trailer cannot tell a loose first act from a
    locked third one, and that difference is what an act break sounds like.
    """
    return [round(fraction_on([c for c in cuts if start <= c < end], grid, tol), 3)
            for start, end in bounds]


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
           lines_lu: list[float] = (), fresh: list[str] | None = None,
           shape: dict | None = None) -> QCReport:
    """The QCReport from the measured grid, the detected cuts, the loudness,
    each line's LU over the ducked bed, whether any picture in the cut is one
    the viewer has already seen -- and `shape`, everything about the master
    that an average cannot say (`measure_shape`).  Without a shape the report
    carries the safe defaults, so a caller that measures nothing claims
    nothing."""
    title_at = planned_cuts(plan)[-1]
    inside = graded(seen, found)
    return QCReport(
        cuts=len(seen), cuts_on_beat=fraction_on(inside, on_music(found)),
        cuts_on_downbeat=fraction_on(inside, sorted(set(found.downbeats) | set(level_zero(found)))),
        cuts_on_L0=fraction_on(level_zero(found), seen),
        on_cap_fraction=on_cap_fraction(act_caps_of(plan["shots"], found.bar), found.bar),
        title_on_downbeat=any(abs(title_at - d) <= ON_GRID for d in found.downbeats),
        integrated_lufs=loud[0], true_peak=loud[1], unbound_shots=len(plan_unbound(plan)),
        reused_shots=reused_shots(plan["shots"]),
        stale_shots=stale_shots(plan["shots"], fresh),
        line_over_bed_lu=list(lines_lu), grid=found.grid, **(shape or {}))


def master_of(out_dir: Path) -> Path:
    return next(out_dir.glob("TRAILER-*.mp4"))


def measure_shape(out_dir: Path, video: Path, plan: dict, cuts: list[float],
                  found: Metre) -> dict:
    """Everything about the master that an average cannot say.

    One ebur128 pass over the delivered file gives both loudness windows; the
    mix's own sheet gives the line windows and the point the bed was stopped;
    the ducked bed beside the master gives what the bed did under each line.
    """
    readings = trailer_assemble.loudness_readings(video)
    if not readings:
        return {}
    heard = [(t, m) for t, m, _ in readings]
    sheet = level_sheet(out_dir)
    windows = sheet_windows(sheet, out_dir=out_dir)
    picture = planned_cuts(plan)[-1]
    hard_out = float(sheet["hard_out"]) if sheet.get("hard_out") else picture
    hit = title_moment(hard_out)[1]
    runs = music_only_runs(heard, windows, picture)
    ducked = out_dir / f"{video.stem}.bed-ducked.wav"
    bed = trailer_assemble.momentary(ducked) if ducked.exists() else []
    shapes = [trailer_assemble.line_shape(out_dir / row["rel_path"]) for row in sheet["lines"]]
    return {"music_only_fraction": music_only_fraction(runs, picture),
            "longest_music_only_s": longest_music_only(runs),
            "final_music_only_s": final_music_only(runs),
            "speech_occupancy": speech_occupancy(windows, picture),
            "speech_target": speech_target(picture),
            "peak_position": peak_position([(t, s) for t, _, s in readings], picture),
            "act3_over_act2_lu": act_over_act(heard, act_bounds(picture)),
            "pre_title_silence_s": longest_under(heard, hard_out, hit, HARD_OUT_AFTER),
            "hard_out": hard_out_ok(heard, hard_out),
            "title_hit_lu": title_hit_lu(heard, hit),
            "line_tp": [tp for tp, _, _ in shapes],
            "line_flat_factor": [flat for _, flat, _ in shapes],
            "line_crest_db": [crest for _, _, crest in shapes],
            "bed_under_line_lu": bed_under_lines(bed, windows) if bed else [],
            "cuts_on_beat_by_act": on_beat_by_act(cuts, on_music(found), act_bounds(picture))}


def qc(out_dir: Path, detect: Callable = scene_cuts, track: beatmap.Tracker | None = None,
       measure: Callable = beatmap.metre, loud: Callable = loudness,
       threshold: float = SCENE_THRESHOLD, lines: Callable = line_over_bed,
       fresh: Callable = fresh_shots, shape: Callable | None = measure_shape) -> QCReport:
    """Measure the master in `out_dir`, write qc.json beside it, return the report.

    The master's own audio is what the tracker reads -- `beatmap.decode`
    takes any container ffmpeg can open, so no separate extraction step.
    """
    video = master_of(out_dir)
    plan = json.loads((out_dir / "plan.json").read_text(encoding="utf-8"))
    seen = detect(video, threshold=threshold)
    found = measure(video, seed=0, rel_path=video.name, track=track)
    measured = shape(out_dir, video, plan, seen, found) if shape else None
    result = report(plan, found, seen, loud(video), lines(out_dir), fresh(out_dir), measured)
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
