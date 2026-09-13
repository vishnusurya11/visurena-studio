"""Motion energy per take: mean absolute frame difference in 0.25 s bins, and
the spans where the picture is effectively frozen (energy below FROZEN for
at least MIN_SPAN seconds).  Free.  Usage: python motion_scan.py <takes_dir> <out.json>"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

FPS = 8
FROZEN = 1.5      # mean |diff| on 0-255 grey at 96x168, per frame step
MIN_SPAN = 0.75   # seconds


def frames(video: Path) -> np.ndarray:
    w, h = 96, 168
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-vf", f"fps={FPS},scale={w}:{h}",
                          "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.uint8).reshape(-1, h, w).astype(np.float32)


def energy(fr: np.ndarray) -> list[float]:
    return [float(np.abs(fr[i + 1] - fr[i]).mean()) for i in range(len(fr) - 1)]


def frozen_spans(e: list[float]) -> list[tuple[float, float]]:
    out, start = [], None
    for i, v in enumerate(e + [99.0]):
        if v < FROZEN and start is None:
            start = i
        elif v >= FROZEN and start is not None:
            if (i - start) / FPS >= MIN_SPAN:
                out.append((round(start / FPS, 2), round(i / FPS, 2)))
            start = None
    return out


def main(takes_dir: Path, out: Path) -> None:
    report = {}
    for video in sorted(takes_dir.glob("T??.mp4")):
        e = energy(frames(video))
        spans = frozen_spans(e)
        report[video.stem] = {"seconds": round(len(e) / FPS, 2), "mean_energy": round(float(np.mean(e)), 2),
                              "frozen_spans": spans, "frozen_s": round(sum(b - a for a, b in spans), 2),
                              "energy_per_quarter_s": [round(x, 1) for x in e[::2]]}
        print(f"{video.stem}: {report[video.stem]['seconds']:5.1f}s energy {report[video.stem]['mean_energy']:5.2f} "
              f"frozen {report[video.stem]['frozen_s']:4.1f}s {spans}", flush=True)
    out.write_text(json.dumps(report, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
