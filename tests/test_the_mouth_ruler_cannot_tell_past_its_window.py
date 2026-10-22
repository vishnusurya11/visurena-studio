"""The mouth ruler says "cannot tell" when its strongest peak lies at or past its +-WINDOW search.

Skeptic 2026-10-21 (finding 3): delivered Jekyll ep01 T19 read 0 f at corr 0.307 inside +-12 f,
just over the 0.3 floor, and the row said in sync; searched +-20 or +-40 f its peak is +16 f at
0.388.  A mouth 12-30 f off read exactly +-12 on 26-53 % of synthetic tries, reported measured.
The window clipped the peak; it did not remove the fold.  The ruler now LOOKS +-GUARD frames and
trusts an in-window read only when the wider search peaks inside the window too.

The real series are FaceMesh apertures recorded on the bench renders (tests/fixtures/mouth/
exam_facemesh.json) against their line's per-frame |sample| mean (exam_lines.json): the line
z-scored is exactly `mouth.voice_envelope` at hop 1/24 s.  Nothing decodes video or opens a model.
"""
import json
from pathlib import Path

import numpy as np
import pytest

from studio.measure import mouth

FIX = Path(__file__).resolve().parent / "fixtures" / "mouth"


def recorded(render: str) -> tuple[np.ndarray, np.ndarray]:
    """(aperture with nan, the render's line as the ruler's voice) for one bench render."""
    ap = json.loads((FIX / "exam_facemesh.json").read_text(encoding="utf-8"))["series"][render]
    d = json.loads((FIX / "exam_lines.json").read_text(encoding="utf-8"))
    line = np.array(d["lines"][str(d["renders"][render]["take"])], dtype=float)
    return np.array([np.nan if v is None else v for v in ap], dtype=float), mouth.zscore(line)


def gated(n: int, k: int) -> tuple[np.ndarray, np.ndarray]:
    """(mouth, voice): three phrases, the mouth open on them k frames late, a little jitter."""
    voice = np.zeros(n)
    for a, b in ((10, 34), (48, 70), (86, 104)):
        voice[a:b] = 1.0
    ap = np.roll(voice, k)
    ap[:k] = 0.0
    return 0.05 + 0.3 * ap + np.random.default_rng(k).normal(0, 0.02, n), mouth.zscore(voice)


def test_delivered_t19_is_cannot_tell_not_in_sync():
    """Its in-window read was 0 f at 0.307; the peak past the window (+16 f) is the stronger."""
    got = mouth.lag(*recorded("T19_A_s1"))
    assert got["measured"] is False and "past" in got["why"]
    assert got["peak_frames"] > mouth.WINDOW and mouth.row(got).value is None


@pytest.mark.parametrize("render, frames", [("T22_A_s1", 8), ("T25_A_s1", -1)])
def test_a_peak_inside_the_window_still_reads(render, frames):
    got = mouth.lag(*recorded(render))
    assert got["measured"] is True and got["lag_frames"] == frames


@pytest.mark.parametrize("k", [14, 16, 20, 26])
def test_a_mouth_late_past_the_window_is_never_measured(k):
    """Unmeasured either way: past the floor its peak is named, under it there is no correlation."""
    ap, voice = gated(124, k)
    got, far = mouth.lag(ap, voice), mouth.past_window(mouth.smooth(ap), voice)
    assert got["measured"] is False and abs(far[0] - k) <= 2
    assert got.get("peak_frames", far[0]) == far[0]


def test_a_mouth_late_inside_the_window_reads_its_lag():
    got = mouth.lag(*gated(124, 6))
    assert got["measured"] is True and abs(got["lag_frames"] - 6) <= 1


def test_the_guard_looks_past_the_window():
    assert mouth.GUARD >= 2 * mouth.WINDOW
    assert mouth.past_window(*gated(124, 16)) is not None and mouth.past_window(*gated(124, 6)) is None
