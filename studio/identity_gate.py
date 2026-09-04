"""The identity gate for reference sheets and rendered clips.

`studio.identity` scores a pair and says which backbones may ship; this
module is the plumbing around it that an unattended step needs: the two
shippable models fetched once from the OpenCV zoo, a file read into one unit
vector, a cast of vectors reduced to the pairs a recogniser cannot tell
apart, and frames sampled from a clip past the reference leak at its head.
Sessions are passed in, so every caller can be tested without a model.
"""
from __future__ import annotations

import subprocess
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np

from studio.identity import SFACE, Recogniser, align, cosine, detect, embed, verdict

MODEL_URLS = {
    "yunet.onnx": "https://github.com/opencv/opencv_zoo/raw/main/models/"
                  "face_detection_yunet/face_detection_yunet_2023mar.onnx",
    "sface.onnx": "https://github.com/opencv/opencv_zoo/raw/main/models/"
                  "face_recognition_sface/face_recognition_sface_2021dec.onnx",
}
MODELS_DIR = Path("models/identity")
HEAD_LEAK_SECONDS = 1.0
"""H3 opens on its reference for roughly a second; a frame from there scores
the sheet, not the shot."""


@dataclass
class Sessions:
    detector: object
    recogniser: object


def _download(url: str, dest: Path) -> None:
    urllib.request.urlretrieve(url, dest)


def ensure_models(models_dir: Path = MODELS_DIR,
                  fetch: Callable[[str, Path], None] = _download) -> dict[str, Path]:
    """Both shippable models on disk, fetched only when missing."""
    models_dir.mkdir(parents=True, exist_ok=True)
    paths = {}
    for name, url in MODEL_URLS.items():
        dest = models_dir / name
        if not dest.exists():
            fetch(url, dest)
        paths[name] = dest
    return paths


def open_sessions(models: dict[str, Path]) -> Sessions:
    import cv2
    import onnxruntime

    detector = cv2.FaceDetectorYN.create(str(models["yunet.onnx"]), "", (320, 320))
    recogniser = onnxruntime.InferenceSession(str(models["sface.onnx"]),
                                              providers=["CPUExecutionProvider"])
    return Sessions(detector, recogniser)


def embed_image(sessions: Sessions, image: np.ndarray,
                using: Recogniser = SFACE) -> tuple[np.ndarray | None, int]:
    """The largest face as a unit vector, plus its width in pixels."""
    faces = detect(sessions.detector, image)
    if not faces:
        return None, 0
    box, landmarks = faces[0]
    return embed(sessions.recogniser, align(image, landmarks), using), int(box[2])


def embed_file(sessions: Sessions, path: Path) -> tuple[np.ndarray | None, int]:
    from PIL import Image

    return embed_image(sessions, np.asarray(Image.open(path).convert("RGB")))


def worst_against(vector: np.ndarray, bound: dict[str, np.ndarray]) -> tuple[str | None, float]:
    """The bound face this one is closest to -- the pair the gate judges."""
    if not bound:
        return None, 0.0
    scored = {who: cosine(vector, other) for who, other in bound.items()}
    who = max(scored, key=scored.get)
    return who, scored[who]


def collisions(vectors: dict[str, np.ndarray], face_px: dict[str, int],
               using: Recogniser = SFACE) -> list[dict]:
    """Every pair the recogniser calls the same person, largest score first."""
    names = sorted(vectors)
    found = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            score = cosine(vectors[a], vectors[b])
            if verdict(score, min(face_px[a], face_px[b]), using) == "fail":
                found.append({"a": a, "b": b, "similarity": round(score, 3)})
    return sorted(found, key=lambda f: -f["similarity"])


def frame_times(seconds: float, count: int = 3, head: float = HEAD_LEAK_SECONDS) -> list[float]:
    """Sample points spread over the clip, none inside the head leak."""
    usable = max(seconds - head, 0.1)
    return [round(head + usable * (i + 0.5) / count, 3) for i in range(count)]


def frame_at(video: Path, seconds: float, dest: Path) -> Path:
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{seconds:.3f}", "-i", str(video),
                    "-frames:v", "1", str(dest)], check=True)
    return dest


def clip_identity(sessions: Sessions, video: Path, seconds: float, reference: np.ndarray,
                  work: Path, grab: Callable[[Path, float, Path], Path] = frame_at
                  ) -> tuple[float | None, int]:
    """Best similarity of any sampled frame to the reference, and its face size."""
    work.mkdir(parents=True, exist_ok=True)
    best: tuple[float | None, int] = (None, 0)
    for when in frame_times(seconds):
        vector, px = embed_file(sessions, grab(video, when, work / f"{when:.2f}.png"))
        if vector is not None and (best[0] is None or cosine(vector, reference) > best[0]):
            best = (cosine(vector, reference), px)
    return best
