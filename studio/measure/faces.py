"""Faces: who, and whether two are one man.  facenet (VGGFace2) says who.

The measured numbers decide the model (docs/calibration/identity.md): same
person 0.73-0.94, cast-vs-cast 0.20 / 0.08 / -0.15, the strangers 0.43 to
-0.04, the one true drift 0.72 against real pairs >= 0.81.  The walls live in
`identity_gate` (READABLE, FRONTAL, MATCH, STRANGER, DRIFT); this module is
the measurer behind them and the clone pair-finder.  Under READABLE an
embedding is noise (8-10 % faces scored 0.46-0.72 against their own sheet),
so a small pair is compared as pictures: the 64x64 zero-mean cosine of the two
crops, and identical renders score >= STRUCTURAL.

`detect=` and `embed=` are injectable; the facenet import is lazy and only
`embedder()` performs it.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

from studio import identity_gate

STRUCTURAL = 0.9
"""64x64 zero-mean cosine at which two small face crops are one render."""
SIG_SIDE = 64
FACE_SIDE = 160
"""InceptionResnetV1's input side."""
SAMPLE_AT = (0.02, 0.25, 0.5, 0.75, 0.98)
"""Where in a take the frames are read when `samples` is left at the default;
`identity_gate.observe` spreads `samples` evenly otherwise."""


def _pil(picture) -> Image.Image:
    if isinstance(picture, Image.Image):
        return picture
    return Image.fromarray(np.asarray(picture))


def structure(crop) -> np.ndarray:
    """The crop as a 64x64 grey, zero-mean unit vector."""
    a = np.asarray(_pil(crop).convert("L").resize((SIG_SIDE, SIG_SIDE)), dtype=float)
    a = a - a.mean()
    return (a / (np.linalg.norm(a) + 1e-9)).ravel()


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.asarray(a) @ np.asarray(b) / ((np.linalg.norm(a) * np.linalg.norm(b)) or 1e-9))


def comparable(a: dict, b: dict) -> str | None:
    """How two faces may be compared: facenet when both are readable, the
    structural signature when either is under READABLE, nothing otherwise."""
    if a["h"] >= identity_gate.READABLE and b["h"] >= identity_gate.READABLE:
        return "facenet" if a.get("vec") is not None and b.get("vec") is not None else None
    return "structure" if a.get("sig") is not None and b.get("sig") is not None else None


def clone_pairs(faces: list[dict]) -> list[dict]:
    """Pairs of faces in one frame that are one man: {i, j, cosine, by}."""
    out = []
    for i in range(len(faces)):
        for j in range(i + 1, len(faces)):
            by = comparable(faces[i], faces[j])
            if by is None:
                continue
            key, wall = ("vec", identity_gate.DRIFT) if by == "facenet" else ("sig", STRUCTURAL)
            c = cosine(faces[i][key], faces[j][key])
            if c >= wall:
                out.append({"i": i, "j": j, "cosine": round(c, 3), "by": by})
    return out


def yaw(landmarks) -> float:
    """The nose's offset from the eye midpoint, in eye distances (0 frontal)."""
    (lx, ly), (rx, ry), (nx, _) = landmarks[0], landmarks[1], landmarks[2]
    eye = float(np.hypot(rx - lx, ry - ly)) or 1e-9
    return round(abs(nx - (lx + rx) / 2) / eye, 3)


def largest(found: list[dict]) -> dict:
    return max(found, key=lambda f: f["box"][3] - f["box"][1])


def _crop(rgb: np.ndarray, box) -> np.ndarray:
    h, w = rgb.shape[:2]
    x1, y1, x2, y2 = (int(round(v)) for v in box)
    x1, y1, x2, y2 = max(0, x1), max(0, y1), min(w, max(x1 + 1, x2)), min(h, max(y1 + 1, y2))
    return np.asarray(Image.fromarray(rgb[y1:y2, x1:x2]).resize((FACE_SIDE, FACE_SIDE)))


def embedder(device: str = "cpu"):
    """(detect, embed) from facenet-pytorch: MTCNN boxes + five landmarks, and
    VGGFace2 unit vectors.  Weights: MTCNN in the package, the resnet cached
    under the user's torch checkpoints."""
    import torch
    from facenet_pytorch import MTCNN, InceptionResnetV1
    mtcnn = MTCNN(keep_all=True, device=device)
    resnet = InceptionResnetV1(pretrained="vggface2").eval()

    def detect(rgb: np.ndarray) -> list[dict]:
        boxes, probs, points = mtcnn.detect(Image.fromarray(rgb), landmarks=True)
        if boxes is None:
            return []
        return [{"box": [float(v) for v in b], "landmarks": p.tolist(), "score": float(s)}
                for b, s, p in zip(boxes, probs, points)]

    def embed(rgb: np.ndarray, box) -> np.ndarray:
        t = torch.from_numpy(_crop(rgb, box).copy()).permute(2, 0, 1).float()
        with torch.no_grad():
            v = resnet(((t - 127.5) / 128.0)[None])[0].numpy()
        return v / (np.linalg.norm(v) or 1e-9)
    return detect, embed


def bank_of(sheets: dict, detect, embed) -> dict[str, list[np.ndarray]]:
    """Per character, the vector of the largest face on each of their sheets."""
    bank: dict[str, list[np.ndarray]] = {}
    for who, paths in sheets.items():
        for path in (paths if isinstance(paths, (list, tuple)) else [paths]):
            rgb = np.asarray(Image.open(path).convert("RGB"))
            found = detect(rgb)
            if found:
                bank.setdefault(who, []).append(embed(rgb, largest(found)["box"]))
    return bank


def score(vec: np.ndarray, bank: dict[str, list[np.ndarray]]) -> dict[str, float]:
    """Max cosine per character over their sheets."""
    return {who: round(max(cosine(vec, v) for v in vecs), 3) for who, vecs in bank.items() if vecs}


def segment_of(k: int, segments: list) -> int:
    """Which pinned segment sample `k` falls in; `segments` lists segment starts."""
    return max(0, sum(1 for s in segments if s <= k) - 1)


def observe(frames: list[np.ndarray], segments: list, bank: dict, detect, embed) -> list[identity_gate.Face]:
    """Every face in every sampled frame, embedded and scored against the bank."""
    out = []
    for k, frame in enumerate(frames):
        fh = frame.shape[0]
        for f in detect(frame):
            vec = embed(frame, f["box"])
            out.append(identity_gate.Face(k=k, h=round((f["box"][3] - f["box"][1]) / fh, 3),
                                          scores=score(vec, bank), vec=vec,
                                          yaw=yaw(f["landmarks"]), seg=segment_of(k, segments)))
    return out


def sample_shares(samples: int):
    """Where in the take (as shares of its length) the `samples` frames are read."""
    return SAMPLE_AT if samples == len(SAMPLE_AT) else tuple(np.linspace(0.02, 0.98, samples))


def sample_frames(video: Path, samples: int) -> list[np.ndarray]:
    """`samples` RGB frames spread evenly through the take."""
    import cv2
    cap = cv2.VideoCapture(str(video))
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    at = sample_shares(samples)
    out = []
    for share in at:
        cap.set(cv2.CAP_PROP_POS_FRAMES, min(n - 1, int(share * n)))
        ok, bgr = cap.read()
        if ok:
            out.append(bgr[:, :, ::-1].copy())
    cap.release()
    return out
