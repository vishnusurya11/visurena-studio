#!/usr/bin/env python
"""Phase-0 bench faults, counted as faults (not a pass/fail gate), per take:

  clones     frames with more big faces (>= people_count.BIG_FACE of frame height) than
             staged character sheets -- the duplicate-figure count
  identity   facenet: median best cosine of readable faces to the staged sheets, and
             how many read as strangers (< identity_gate.STRANGER)
  lag        mux lag of the take's soundtrack against the staged voice wav (av_sync)
  still      share of 0.5 s bins the eye reads as a still (motion_gate.STILL)
  kbps       the file's video bitrate (ffprobe)

    uv run --no-sync python scripts/bench/faults.py <out.json> <video>=<ran graph> ...
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from studio import people_count  # noqa: E402

INPUT = Path("D:/Projects/KingdomOfViSuReNa/alpha/ComfyUI_windows_portable/ComfyUI/input")


def sheets_of(graph: dict) -> list[str]:
    return [n["inputs"]["image"] for n in graph.values()
            if n.get("class_type") == "LoadImage" and n["inputs"]["image"].startswith("sheet")]


def voice_of(graph: dict) -> str | None:
    a = next((n["inputs"]["audio"] for n in graph.values() if n.get("class_type") == "LoadAudio"), None)
    return a if a and a.startswith("voice") else None


def clone_frames(per_frame: list[list[float]], planned: int) -> int:
    return sum(1 for f in per_frame if people_count.clones(f, planned))


def kbps(video: Path) -> float:
    """Container bitrate (file bytes over cv2 duration): no ffprobe on this machine."""
    import cv2
    cap = cv2.VideoCapture(str(video))
    seconds = cap.get(cv2.CAP_PROP_FRAME_COUNT) / (cap.get(cv2.CAP_PROP_FPS) or 24)
    cap.release()
    return round(video.stat().st_size * 8 / 1000 / seconds, 0) if seconds else 0.0


def still(video: Path) -> float:
    from studio import motion_gate as mg
    return mg.still_share(mg.bin_means(mg.block_max(mg.frames(video))))


def faces(video: Path, graph: dict, detect, embed) -> dict:
    from studio import identity_gate as ig
    from studio.measure.faces import bank_of, largest, sample_frames, score  # noqa: F401
    bank = bank_of({s: INPUT / s for s in sheets_of(graph)}, detect, embed)
    heights, best = [], []
    for rgb in sample_frames(video, 12):
        found = detect(rgb)
        heights.append([(f["box"][3] - f["box"][1]) / rgb.shape[0] for f in found])
        for f in found:
            if (f["box"][3] - f["box"][1]) / rgb.shape[0] >= ig.READABLE and bank:
                best.append(max(score(embed(rgb, f["box"]), bank).values()))
    planned = len(sheets_of(graph))
    return {"planned": planned, "clone_frames": clone_frames(heights, planned), "frames": len(heights),
            "id_median": round(float(np.median(best)), 3) if best else None,
            "strangers": sum(b < ig.STRANGER for b in best), "readable": len(best)}


def measure(video: Path, graph: dict, detect, embed) -> dict:
    from studio import av_sync
    v = voice_of(graph)
    lag = round(av_sync.take_lag(video, INPUT / v), 3) if v else None
    return {**faces(video, graph, detect, embed), "lag": lag, "still": still(video), "kbps": kbps(video)}


def main(argv: list[str]) -> None:
    from studio.measure.faces import embedder
    detect, embed = embedder()
    res = {}
    for pair in argv[1:]:
        video, graph = pair.split("=", 1)
        res[video] = measure(Path(video), json.loads(Path(graph).read_text("utf-8")), detect, embed)
        print(video, res[video], flush=True)
    Path(argv[0]).write_text(json.dumps(res, indent=1), "utf-8")


if __name__ == "__main__":
    main(sys.argv[1:])
