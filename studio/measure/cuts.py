"""A second vote on an unplanned cut inside a take.

The brightness step (`take_coherence.hard_cut`) missed a switch between two
pictures of the same brightness; the picture jump (`take_jump.min_step`) was
built for that; PySceneDetect's adaptive detector (an HSV content score
against its rolling mean, robust to a pan) is the third reader.  Two of the
three make the cut HARD; one alone is an advisory.  The detector is fed
numpy frames, so the take is decoded once, by the caller.
"""
from __future__ import annotations

import numpy as np

ADAPTIVE_THRESHOLD = 3.0
MIN_SCENE_LEN = 2
VOTES_NEEDED = 2
FITTED_ON = "the two named jumps and three named brightness cuts of one book; scenedetect at its default 3.0"


def scene_cuts(frames, fps: int = 24, threshold: float = ADAPTIVE_THRESHOLD) -> list[int]:
    """Frame indices where PySceneDetect's adaptive detector sees a new scene."""
    from scenedetect import FrameTimecode
    from scenedetect.detectors import AdaptiveDetector

    det = AdaptiveDetector(adaptive_threshold=threshold, min_scene_len=MIN_SCENE_LEN)
    found = []
    for k, f in enumerate(frames):
        found += det.process_frame(FrameTimecode(k, float(fps)), as_bgr(f))
    found += det.post_process(FrameTimecode(len(frames), float(fps)))
    return sorted({int(t.frame_num) for t in found})


def as_bgr(frame: np.ndarray) -> np.ndarray:
    """Three-channel uint8 for the detector; a grey frame is stacked."""
    f = np.asarray(frame)
    if f.ndim == 2:
        f = np.repeat(f[:, :, None], 3, axis=2)
    return np.ascontiguousarray(f[:, :, ::-1], dtype=np.uint8)


def unplanned(cut_frames: list[int], anchors: list, tol: int = 6) -> list[int]:
    """The detected cuts not within `tol` frames of an internal pin."""
    pins = [int(f) for _, f in anchors or [] if int(f) > 0]
    return [c for c in cut_frames if not any(abs(c - p) <= tol for p in pins)]


def vote(jump: bool, step: bool, scene: bool) -> dict:
    votes = {"jump": bool(jump), "step": bool(step), "scene": bool(scene)}
    n = sum(votes.values())
    return {"votes": votes, "count": n, "cut": n >= VOTES_NEEDED, "fitted_on": FITTED_ON}


def row(v: dict | None):
    """HARD on two votes, advisory on one, quiet on none."""
    from studio.take_verdict import Gate

    if not v:
        return Gate("cut-vote", None, True, False, "not measured")
    who = "+".join(k for k, yes in v["votes"].items() if yes) or "none"
    if v["cut"]:
        return Gate("cut-vote", v["count"], False, True, f"{who} HARD: an unplanned cut", 40.0)
    return Gate("cut-vote", v["count"], v["count"] == 0, False, who, 10.0 * v["count"])
