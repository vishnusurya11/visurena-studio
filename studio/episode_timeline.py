"""Cut the picture to the voice: shot times derived from the measured lines.

    shot.seconds = HANDLE + sum(measured line seconds) + BREATH x (lines - 1)
                   + HANDLE + beat_s + coda_s

Runtime is the cumulative sum.  Seconds enter once, measured from the files
(`lines/lines.json`), and everything downstream -- panels, takes, the cut,
QC -- reads `placed.json`.  Nothing is ever scheduled or dropped afterwards.
"""
from __future__ import annotations

from studio.episode_spec import BREATH, HANDLE, Episode

FPS = 24


def on_frame(seconds: float) -> float:
    """Seconds snapped UP to a whole frame at 24 fps.

    The cut trims every segment to whole frames, so a fractional shot length
    drifts the cut from the placed time -- measured 0.12-0.16 s late over
    twelve shots on the first audio-first master, which put the driven lips a
    few frames off their own line.  Snapping here makes the placed time and
    the cut frame the same number."""
    import math

    return math.ceil(seconds * FPS - 1e-9) / FPS


def place(episode: Episode, measured: dict[int, float]) -> dict:
    """`measured` maps line index -> seconds of the rendered file."""
    shots, lines, t = [], [], 0.0
    for shot in episode.shots:
        start, cursor = t, t + HANDLE
        for k, line in enumerate(episode.lines_of(shot.index)):
            if k:
                cursor += BREATH
            lines.append({"index": line.index, "kind": line.kind, "speaker": line.speaker,
                          "text": line.text, "shot": shot.index, "at": round(cursor, 3),
                          "seconds": measured[line.index]})
            cursor += measured[line.index]
        seconds = on_frame(cursor + HANDLE + shot.beat_s + shot.coda_s - start)
        end = start + seconds
        shots.append({"index": shot.index, "t_start": round(start, 6), "t_end": round(end, 6),
                      "seconds": round(seconds, 6), "lane": lane_of(episode, shot.index),
                      "cuts": [round(start + c.at_s, 3) for c in shot.cuts]})
        t = end
    return {"duration_s": round(t, 6), "shots": shots, "lines": lines}


def lane_of(episode: Episode, shot_index: int) -> str:
    """`dialogue` takes are driven by the line's audio (lips move); the rest are silent i2v."""
    return "dialogue" if any(l.kind == "dialogue" for l in episode.lines_of(shot_index)) else "narration"


def holes(placed: dict, longer_than: float = 1.5) -> list[tuple[float, float]]:
    """Stretches with no voice longer than `longer_than`, before the last line."""
    out, end = [], None
    ordered = sorted(placed["lines"], key=lambda l: l["at"])
    for line in ordered:
        if end is not None and line["at"] - end > longer_than:
            out.append((round(end, 2), round(line["at"], 2)))
        end = max(end or 0.0, line["at"] + line["seconds"])
    return out


def short_subshots(placed: dict, minimum: float = 2.5) -> list[int]:
    """Shots whose last sub-shot, measured, would run shorter than `minimum`."""
    return [s["index"] for s in placed["shots"] if s.get("cuts") and s["t_end"] - s["cuts"][-1] < minimum]


def misaligned(placed: dict) -> list[str]:
    """THE SYNC RULE, checked: every line sits fully inside its own shot with
    the handles on both sides, and every dialogue line starts exactly one
    handle after its shot's first frame (where the driven mouth opens).
    Owner-approved on the first audio-first master (2026-09-10)."""
    shots = {s["index"]: s for s in placed["shots"]}
    faults = []
    for line in placed["lines"]:
        shot = shots[line["shot"]]
        start, end = line["at"], line["at"] + line["seconds"]
        if start < shot["t_start"] + HANDLE - 1e-3 or end > shot["t_end"] - HANDLE + 1e-3:
            faults.append(f"line {line['index']} ({start:.2f}-{end:.2f}) leaves shot "
                          f"{shot['index']} ({shot['t_start']:.2f}-{shot['t_end']:.2f})")
        if line["kind"] == "dialogue" and abs(start - shot["t_start"] - HANDLE) > 1e-3:
            faults.append(f"dialogue line {line['index']} does not start one handle into its shot")
    return faults
