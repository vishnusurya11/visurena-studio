"""The mouth ruler must find a mouth moved a KNOWN number of frames off its line.

GAVEL 2026-10-21 (H3 `<Audio 1>` lip-sync bench, ruling 11): `voice_envelope`
returns a z-scored envelope, and `lag` passed it through `av_sync.envelope`
again, whose `np.abs` folds the line's silences (z < 0) into bumps.  A mouth
open on the words 5 frames late read +19 f; delivered T22 read +13 f and T19
+17 f.  The voice is a recorded line (voice_22, its first 4.5 s, 8 kHz mono,
in tests/fixtures/mouth/); the mouth is open while that line is voiced, moved
k frames, with landmark jitter.  Nothing here decodes video or opens a model.
"""
import wave
from pathlib import Path

import numpy as np
import pytest

from studio.measure import mouth

WAV = Path(__file__).resolve().parent / "fixtures" / "mouth" / "voice_22_head.wav"


def line() -> tuple[np.ndarray, int]:
    with wave.open(str(WAV)) as w:
        raw = w.readframes(w.getnframes())
        return np.frombuffer(raw, np.int16).astype(float) / 32768, w.getframerate()


def voiced(wav: np.ndarray, sr: int) -> np.ndarray:
    """1 on the frames the line is voiced, 0 in its silences."""
    step = sr // mouth.FPS
    n = len(wav) // step
    e = np.abs(wav[: n * step]).reshape(n, step).mean(axis=1)
    return (e > e.min() + 0.08 * (e.max() - e.min())).astype(float)


def mouth_on(gate: np.ndarray, k: int, seed: int = 0) -> np.ndarray:
    """An aperture open on the voiced frames, k frames late, with landmark jitter."""
    ap = np.roll(gate, k)
    if k > 0:
        ap[:k] = 0.0
    elif k < 0:
        ap[k:] = 0.0
    return 0.05 + 0.3 * ap + np.random.default_rng(seed).normal(0, 0.03, len(ap))


@pytest.mark.parametrize("k", [-10, -6, -2, 0, 3, 5, 8, 10])
def test_a_mouth_moved_k_frames_off_the_line_reads_k(k):
    """Within one frame, half the row's tolerance: an open/shut mouth against a
    decaying envelope peaks flat across two frames.  The fold read k + 14 or 15."""
    wav, sr = line()
    got = mouth.lag(mouth_on(voiced(wav, sr), k), mouth.voice_envelope(wav, sr))
    assert got["measured"] is True and abs(got["lag_frames"] - k) <= 1


def test_a_mouth_that_is_the_voice_correlates_with_it():
    """The fold's other face: an aperture that IS the line's envelope read +1 f, corr 0.43."""
    wav, sr = line()
    voice = mouth.voice_envelope(wav, sr)
    got = mouth.lag(voice - voice.min(), voice)
    assert got["lag_frames"] == 0 and got["corr"] > 0.9


def test_the_search_stays_inside_its_window():
    """A mouth 20 f off is not chased onto the next syllable, nor clipped to +-WINDOW and reported:
    its peak lies past the window, so the ruler cannot tell (skeptic 2026-10-21, finding 3)."""
    wav, sr = line()
    got = mouth.lag(mouth_on(voiced(wav, sr), 20), mouth.voice_envelope(wav, sr))
    assert 8 <= mouth.WINDOW <= 12 and got["window"] == mouth.WINDOW
    assert got["measured"] is False and "lag_frames" not in got


def test_zscore_keeps_the_sign_and_a_flat_signal_is_zeros():
    z = mouth.zscore(np.array([0.0, 0.0, 0.0, 3.0]))
    assert z[0] < 0 < z[3] and abs(z.mean()) < 1e-9 and abs(z.std() - 1.0) < 1e-6
    assert not mouth.zscore(np.full(5, 0.4)).any()


def test_a_short_overlap_cannot_outscore_the_aligned_one():
    z = mouth.zscore(np.sin(np.arange(48) * 2 * np.pi / 12))
    assert mouth.xcorr_at(z, z, 0) > mouth.xcorr_at(z, z, 12) > 0
    assert mouth.xcorr_at(z, z, 3) == pytest.approx(mouth.xcorr_at(z, z, -3))


def test_best_lag_reads_positive_when_the_first_signal_is_late():
    b = np.zeros(60)
    b[20:30] = 1.0
    late, corr = mouth.best_lag(np.roll(b, 4), b)
    assert late == 4 and corr > 0.9
    assert mouth.best_lag(np.roll(b, -4), b)[0] == -4 and mouth.best_lag(b[:1], b) == (0, 0.0)
