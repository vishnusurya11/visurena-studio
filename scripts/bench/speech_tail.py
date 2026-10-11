#!/usr/bin/env python
"""INVENTED-SPEECH hard check for dialogue arms (owner 2026-10-11; studio/invented_speech.py),
and the owner's review copies with H3's audio replaced by the recorded voice guide.

    uv run --no-sync python scripts/bench/speech_tail.py check <out.json> <video>=<ran graph> ...
    uv run --no-sync python scripts/bench/speech_tail.py review <out_dir> <video>=<ran graph> ...

The guide is the graph's staged LoadAudio voice_* wav in ComfyUI/input; a take
with no voice guide (refs-only, silence) is not a dialogue take and is skipped.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.bench.faults import INPUT, voice_of  # noqa: E402
from studio import invented_speech as inv  # noqa: E402

SR = 16000
MOUTH_FRAMES = 10


def ffmpeg() -> str:
    from studio.take_zoom import ffmpeg_exe
    return ffmpeg_exe()


def audio(path: Path) -> np.ndarray:
    """Any file's first audio stream as 16 kHz mono float32."""
    raw = subprocess.run([ffmpeg(), "-v", "error", "-i", str(path), "-vn", "-ac", "1", "-ar", str(SR),
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def ear(listen):
    """`hear(samples)` over a transcriber that takes a file."""
    def hear(samples: np.ndarray) -> str:
        import soundfile as sf
        with tempfile.TemporaryDirectory() as d:
            clip = Path(d) / "tail.wav"
            sf.write(clip, samples, SR)
            return listen(clip)
    return hear


def lower_face(frames: list[np.ndarray], detect) -> list[np.ndarray]:
    """The lower half of the largest face on the first frame, cut from every frame, grey."""
    found = detect(frames[0]) if frames else []
    if not found:
        return []
    x1, y1, x2, y2 = (int(max(0, v)) for v in max(found, key=lambda f: f["box"][3] - f["box"][1])["box"])
    mid = (y1 + y2) // 2
    return [f[mid:y2, x1:x2].astype(np.float32).mean(axis=2) for f in frames]


def mouth(video: Path, end_s: float, detect) -> float | None:
    """Lower-face motion in the tail over during the line; None without a face or a tail."""
    import cv2
    cap = cv2.VideoCapture(str(video))
    n, fps = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)), cap.get(cv2.CAP_PROP_FPS) or 24
    cap.release()
    cut = min(n - 1, int((end_s + inv.MARGIN_S) * fps))
    if n - cut < 4 or cut < 4:
        return None
    from scripts.bench.rulers import frames
    picks = list(np.linspace(0, cut / n, MOUTH_FRAMES, endpoint=False)) + list(np.linspace(cut / n, 0.999, MOUTH_FRAMES))
    faces = lower_face(frames(video, picks), detect)
    return inv.motion_ratio(faces[:MOUTH_FRAMES], faces[MOUTH_FRAMES:]) if faces else None


def check_one(video: Path, graph: dict, hear, detect=None) -> dict | None:
    v = voice_of(graph)
    if not v:
        return None
    row = inv.check(audio(video), audio(INPUT / v), SR, hear)
    row["mouth_tail_ratio"] = mouth(video, row["line_end_s"], detect) if detect else None
    return row


def review_cmd(video: Path, guide: Path, out: Path) -> list[str]:
    """The take's picture with the recorded voice guide as its sound -- what ships."""
    return [ffmpeg(), "-y", "-v", "error", "-i", str(video), "-i", str(guide), "-map", "0:v:0", "-map", "1:a:0",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", str(out)]


def review(video: Path, graph: dict, out_dir: Path) -> Path | None:
    v = voice_of(graph)
    if not v:
        return None
    out = Path(out_dir) / f"{Path(video).stem}_review.mp4"
    subprocess.run(review_cmd(Path(video), INPUT / v, out), check=True)
    return out


def pairs(argv: list[str]) -> list[tuple[Path, dict]]:
    out = []
    for a in argv:
        v, g = a.split("=", 1)
        out.append((Path(v), json.loads(Path(g).read_text("utf-8"))))
    return out


def main(argv: list[str]) -> None:
    if argv[0] == "review":
        for v, g in pairs(argv[2:]):
            print(review(v, g, Path(argv[1])))
        return
    from scripts.bench.rulers import detector
    from studio.voice_qc import transcriber
    hear, det = ear(transcriber(device="cpu")), detector()
    out = Path(argv[1])
    res = json.loads(out.read_text("utf-8")) if out.exists() else {}
    for v, g in pairs(argv[2:]):
        res[v.stem] = check_one(v, g, hear, det)
        print(v.stem, res[v.stem], flush=True)
        out.write_text(json.dumps(res, indent=1), "utf-8")


if __name__ == "__main__":
    main(sys.argv[1:])
