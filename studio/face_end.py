"""G-FACE-END -- did the push carry the face out of the frame?

Episode 10 (2026-09-16): the reviewer's retakes were faces the push had run out
of the frame -- T05's second render ended on nostrils, T16 and T28 on a crown
cut by the top edge -- and every row passed them.  Zoom measures how far the
picture travelled, not whether the face is whole at the end of it: T13's whole
face at 2.16x reads the same as T05's nostrils at 1.93x.  This row reads ONE
frame, the last frame of the take's first segment (the frame before the second
pin, else the last frame), and asks two things of the largest face on it: its
height against the frame, and whether its box touches an edge.

The detector is OpenCV's YuNet (studio/models/yunet.onnx, 232 KB, from the
OpenCV model zoo; opencv-python-headless in the lock): boxes and five
landmarks, CPU, about 0.3 s a frame at 768.  It is a detector, not a
recogniser -- identity (studio/identity_gate.py) still wants an embedder.

CALIBRATION (docs/calibration/face_end.md; YuNet on the end frame of the first
segment of every ep10 render, kept and superseded; box height / 768, C = the
box touches an edge; reviewer labels from the DQ brief):

    fault   T05_fail2 0.85C   T05_fail1 0.85   T16 0.81C   T25 0.77   T28 0.74C
    keep    T14 0.83C  (the accepted false alarm: a whole close, hair on the edge)
            T27 0.73   T08 0.69   T05 0.68   T22 0.68C   T18 0.63   T13 0.59
            T10 0.51   T07 0.40

The wall at 0.75 -- or clipped from CLIPPED_HARD up -- on a close /
medium_close with a planned face: five hits and one false alarm (T14),
against the zoom wall's three false alarms on the same faults.  Two things
the numbers taught: a box at an edge is composition when it is small and a
face leaving when it is large (T22's Lucy at 0.68 with the hair line on the
top edge is the storyboard's own framing, a KEEP; T28's at 0.74 leaving
frame-left is the fault), which is why the clip trigger has a size floor;
and the margin between them, 0.06, is one take wide -- say so when it moves.
T24, an insert whose hand read as a 0.80 "face", is why the wall needs a
planned face; T29_fail1, the back of a head where a face was staged, is the
advisory.  Free: no GPU, no credit.
"""
from __future__ import annotations

import io
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image

FACE_END_HARD = 0.75
"""Face box height / frame height at which a close has lost its face.  Faults
0.77-0.85 whole, KEEPs <= 0.73 (T14 0.83 clipped is the one exception)."""
CLIPPED_HARD = 0.70
"""A box that touches an edge is a face LEAVING only from this height: T28
0.74 clipped (fault) against T22 0.68 clipped (keep, the cell's own framing).
One take of margin on each side."""
SIZES = {"close", "medium_close"}
"""The plan sizes the wall applies to: a face is the shot, so a face out of the
frame is the shot gone.  A medium with a face at the edge is composition."""
EDGE = 8 / 768
"""A box within this fraction of the frame of an edge touches it (the
analyst's 8 px at 768)."""
SCORE, NMS = 0.5, 0.3
MODEL = Path(__file__).resolve().parent / "models" / "yunet.onnx"
PENALTY_HARD, PENALTY_AWAY = 30.0, 5.0
FRAME_EXT = (".png", ".jpg", ".jpeg")
PNG_SIG = b"\x89PNG\r\n\x1a\n"


# ---- the detector --------------------------------------------------------------

def detector(size: tuple[int, int]):
    """YuNet sized to the frame, or None when OpenCV or the model is missing."""
    try:
        import cv2
        cv2.utils.logging.setLogLevel(cv2.utils.logging.LOG_LEVEL_ERROR)
        if not MODEL.exists():
            return None
        return cv2.FaceDetectorYN.create(str(MODEL), "", size, SCORE, NMS, 5000)
    except Exception:
        return None


def edges_of(x: float, y: float, w: float, h: float, fw: int, fh: int) -> list[str]:
    """The frame edges a box touches."""
    out = []
    if y < EDGE * fh:
        out.append("top")
    if y + h > fh * (1 - EDGE):
        out.append("bottom")
    if x < EDGE * fw:
        out.append("left")
    if x + w > fw * (1 - EDGE):
        out.append("right")
    return out


def faces(rgb: np.ndarray) -> list[dict] | None:
    """Every face on one RGB frame, tallest first; None when there is no model."""
    fh, fw = rgb.shape[:2]
    det = detector((fw, fh))
    if det is None:
        return None
    det.setInputSize((fw, fh))
    _, found = det.detect(np.ascontiguousarray(rgb[:, :, ::-1]))
    out = []
    for r in (found if found is not None else []):
        x, y, w, h = (float(v) for v in r[:4])
        edges = edges_of(x, y, w, h, fw, fh)
        out.append({"h": round(h / fh, 3), "clipped": bool(edges), "edges": edges, "score": round(float(r[-1]), 2),
                    "cx": round((x + w / 2) / fw, 2), "cy": round((y + h / 2) / fh, 2)})
    return sorted(out, key=lambda d: -d["h"])


def largest_face(rgb: np.ndarray) -> dict | None:
    """The tallest face on the frame, or None when there is none (or no model)."""
    got = faces(rgb)
    return got[0] if got else None


# ---- which frame -----------------------------------------------------------------

def end_index(anchors: list) -> int | None:
    """The frame the row reads: the one before the second pin, else None = the last."""
    return int(anchors[1][1]) - 1 if len(anchors) > 1 else None


def frame_at(video: Path, n: int | None) -> np.ndarray:
    """Frame `n` of the take as RGB uint8 (None = the last frame).  A folder of
    images, in name order, serves the same -- that is what the tests use."""
    video = Path(video)
    if video.is_dir():
        names = sorted(p for p in video.iterdir() if p.suffix.lower() in FRAME_EXT)
        return np.asarray(Image.open(names[-1 if n is None else n]).convert("RGB"))
    seek = ["-sseof", "-0.25"] if n is None else []
    pick = [] if n is None else ["-vf", f"select=eq(n\\,{n})", "-frames:v", "1"]
    cmd = ["ffmpeg", "-v", "error", *seek, "-i", str(video), *pick, "-vsync", "0", "-f", "image2pipe", "-vcodec", "png", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    if not raw and n is None:       # a file whose tail will not seek: decode it all, keep the last
        raw = subprocess.run(cmd[:3] + cmd[5:], capture_output=True, check=True).stdout
    return np.asarray(Image.open(io.BytesIO(PNG_SIG + raw.split(PNG_SIG)[-1])).convert("RGB"))


# ---- the verdict -----------------------------------------------------------------

def verdict(face: dict | None, size: str, planned: int):
    """HARD over the wall or clipped on a close / medium_close with a planned
    face; ADVISORY when a face was planned and none is found; ok otherwise."""
    from studio.take_verdict import Gate
    if face is None:
        if planned:
            return Gate("face-at-end", None, False, False, f"no face found ({planned} planned)", PENALTY_AWAY)
        return Gate("face-at-end", None, True, False, "no face, none planned")
    over = face["h"] >= FACE_END_HARD or (face["clipped"] and face["h"] >= CLIPPED_HARD)
    hard = over and planned > 0 and size in SIZES
    note = f"{face['h']:.2f}" + (" clipped " + "/".join(face["edges"]) if face["clipped"] else "")
    return Gate("face-at-end", face["h"], not hard, hard, note, PENALTY_HARD if hard else 0.0)


def row(video: Path, record: dict):
    """The verdict row for one take.  `record` is the take's shots.json entry
    (`anchors`, `size` = the plan size of its first shot, `faces` = the
    planned cast); "not measured" when there is no face model."""
    from studio.take_verdict import Gate
    found = faces(frame_at(video, end_index(record.get("anchors") or [])))
    if found is None:
        return Gate("face-at-end", None, True, False, "not measured")
    return verdict(found[0] if found else None, record.get("size", ""), len(record.get("faces") or []))
