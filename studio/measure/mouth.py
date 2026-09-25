"""The mouth against the words: a lip-aperture envelope cross-correlated with
the wav's envelope, in FRAMES.

`av_sync.take_lag` measures the MUX -- the take's own soundtrack against the
wav that drove it -- and cannot fail.  This reads the MOUTH: MediaPipe
FaceMesh's inner-lip landmarks (13 over 14) per frame, the gap over the eye
distance, smoothed over three frames, and `av_sync.lag_seconds` on the two
per-frame signals (sr 1, hop 1.0: the same correlation, its unit a frame).

Two owner-caught lagging takes against seven passes, unbenched: the row is
ADVISORY, and its cure is the shorter take, never a seed.  A mouth the
landmarker cannot read, or an aperture that does not correlate with the
voice, is "cannot tell" -- it passes nothing.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

from studio import av_sync

UPPER, LOWER, LEFT_EYE, RIGHT_EYE = 13, 14, 33, 263
FPS = 24
SMOOTH = 3
CORR_FLOOR = 0.3
LAG_TOL_FRAMES = 2
READABLE = 0.5
FITTED_ON = "two owner-caught lagging takes against seven passes, unbenched: advisory; the cure is the shorter take"
MODEL = Path(__file__).resolve().parents[1] / "models" / "face_landmarker.task"


def aperture(points) -> float:
    """|upper - lower| over the eye distance; nan with no landmarks."""
    if points is None:
        return float("nan")
    p = np.asarray(points, dtype=float)
    eyes = np.linalg.norm(p[LEFT_EYE] - p[RIGHT_EYE])
    return float(np.linalg.norm(p[UPPER] - p[LOWER]) / (eyes + 1e-9))


def apertures(frames, landmarker) -> np.ndarray:
    """One aperture per frame; nan where the landmarker read no face."""
    return np.array([aperture(landmarker(f)) for f in frames], dtype=float)


def readable(ap: np.ndarray) -> float:
    return float(np.mean(~np.isnan(ap))) if len(ap) else 0.0


def fill(ap: np.ndarray) -> np.ndarray:
    """Unread frames take the mean, so the correlation runs on what was read."""
    out = np.asarray(ap, dtype=float).copy()
    seen = ~np.isnan(out)
    out[~seen] = out[seen].mean() if seen.any() else 0.0
    return out


def smooth(x: np.ndarray, k: int = SMOOTH) -> np.ndarray:
    return np.convolve(x, np.ones(k) / k, mode="same") if len(x) >= k else np.asarray(x, dtype=float)


def voice_envelope(wav: np.ndarray, sr: int, fps: int = FPS) -> np.ndarray:
    """The wav's envelope at one value per frame (`av_sync.envelope`, hop 1/fps)."""
    return av_sync.envelope(wav, sr, 1.0 / fps)


def peak_corr(a: np.ndarray, b: np.ndarray) -> float:
    """The normalised peak of the cross-correlation of two z-scored signals."""
    n = min(len(a), len(b))
    if n < 2:
        return 0.0
    za, zb = av_sync.envelope(a[:n], 1, 1.0), av_sync.envelope(b[:n], 1, 1.0)
    return float(np.correlate(za, zb, mode="full").max() / n)


def lag(ap: np.ndarray, voice: np.ndarray, fps: int = FPS) -> dict:
    """The mouth's lag in frames against the voice; positive when the mouth is late."""
    seen = readable(ap)
    if seen < READABLE:
        return {"measured": False, "why": "no readable face", "readable": seen, "fitted_on": FITTED_ON}
    track = smooth(fill(ap))
    corr = peak_corr(track, voice)
    if corr < CORR_FLOOR:
        return {"measured": False, "why": f"no correlation with the voice ({corr:.2f})", "corr": round(corr, 3),
                "readable": seen, "fitted_on": FITTED_ON}
    frames = int(round(av_sync.lag_seconds(track, voice, 1, 1.0)))
    return {"measured": True, "lag_frames": frames, "lag_s": round(frames / fps, 3), "corr": round(corr, 3),
            "readable": seen, "fitted_on": FITTED_ON}


def row(got: dict | None):
    """Advisory: |lag| within LAG_TOL_FRAMES is ok; unmeasured cannot tell."""
    from studio.take_verdict import Gate

    if not got:
        return Gate("lag", None, True, False, "not measured")
    if not got.get("measured"):
        return Gate("lag", None, True, False, f"cannot tell: {got.get('why', '')}")
    n = got["lag_frames"]
    ok = abs(n) <= LAG_TOL_FRAMES
    note = f"{n:+d}f ({got['lag_s']:+.3f}s) corr {got['corr']:.2f}"
    return Gate("lag", n, ok, False, note, 0.0 if ok else min(30.0, 10.0 * (abs(n) - LAG_TOL_FRAMES)))


def facemesh(model: Path = MODEL):
    """A landmarker callable over RGB frames: (478, 2) normalised points or
    None.  Loads the FaceLandmarker `.task` from `model`; never downloads it."""
    model = Path(model)
    if not model.is_file():
        raise FileNotFoundError(f"no FaceLandmarker model at {model}; put face_landmarker.task there")
    import mediapipe as mp
    from mediapipe.tasks.python import BaseOptions, vision

    lm = vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=str(model)), num_faces=1))

    def read(frame: np.ndarray):
        res = lm.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(frame)))
        if not res.face_landmarks:
            return None
        return np.array([(p.x, p.y) for p in res.face_landmarks[0]], dtype=float)

    return read
