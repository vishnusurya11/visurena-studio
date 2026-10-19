"""A blink moves the eye mask for 5-8 frames; only a run of >= 12 consecutive frame-pairs on a
small face is a sustained eye warp (P07).  Eye excess is advisory in the verdict either way."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.episode import warp_labels as wl  # noqa: E402
from studio import warp_gate as wg  # noqa: E402


def measure(blink: int) -> dict:
    n = 73
    re_ = np.full(n, 1.0)
    re_[20:20 + blink] = 9.0
    rows = {"rf": np.full(n, 1.0), "rb": np.zeros(n), "mf": np.zeros(n), "re": re_}
    return wg.judge(rows, share=1.0, frames=n + 1, face_w=0.05)


def test_a_blink_of_seven_frames_is_neither_a_fail_nor_sustained():
    m = measure(7)
    assert m["state"] in ("pass", "warn") and m["eye_spans"] == [[20, 26]] and not wl.sustained(m)


def test_twelve_frames_of_eye_excess_are_sustained_and_still_only_an_advisory():
    m = measure(12)
    assert wl.sustained(m) and wg.row(m).ok
