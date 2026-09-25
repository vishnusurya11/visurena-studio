"""The mouth-envelope lag is read off FaceMesh lip landmarks against the wav's
envelope.  A mouth the landmarker cannot read, or an aperture that does not
correlate with the voice at all, is "cannot tell": it passes nothing and
fails nothing.  The landmarker is injected; no model is loaded here.
"""
import numpy as np
import pytest

from studio.measure import mouth


def talking(n: int = 72, period: int = 12, seed: int = 0) -> np.ndarray:
    t = np.arange(n)
    return 0.3 + 0.2 * np.clip(np.sin(2 * np.pi * t / period), 0, None) + np.random.default_rng(seed).normal(0, 0.01, n)


def landmarks_of(ap: float) -> np.ndarray:
    pts = np.zeros((478, 2))
    pts[mouth.LEFT_EYE], pts[mouth.RIGHT_EYE] = (0.3, 0.4), (0.7, 0.4)       # eye distance 0.4
    pts[mouth.UPPER], pts[mouth.LOWER] = (0.5, 0.6), (0.5, 0.6 + ap * 0.4)
    return pts


def test_the_aperture_is_the_lip_gap_over_the_eye_distance():
    assert abs(mouth.aperture(landmarks_of(0.25)) - 0.25) < 1e-9
    assert np.isnan(mouth.aperture(None))


def test_frames_with_no_face_read_nan_and_count_as_unreadable():
    frames = [np.zeros((8, 8, 3), np.uint8)] * 10
    ap = mouth.apertures(frames, landmarker=lambda f: None)
    assert ap.shape == (10,) and np.isnan(ap).all()
    assert mouth.readable(ap) == 0.0


def test_an_unreadable_mouth_cannot_tell():
    voice = talking()
    got = mouth.lag(np.full(72, np.nan), voice)
    assert got["measured"] is False and got["why"] == "no readable face"
    row = mouth.row(got)
    assert row.ok and row.value is None and row.note.startswith("cannot tell")


def test_a_mouth_that_does_not_follow_the_voice_cannot_tell():
    flat = np.full(72, 0.3) + np.random.default_rng(1).normal(0, 0.005, 72)
    got = mouth.lag(flat, talking())
    assert got["measured"] is False and got["corr"] < mouth.CORR_FLOOR and "correlat" in got["why"]
    assert mouth.row(got).value is None


def test_a_mouth_on_the_words_reads_zero_lag_and_measured():
    ap = talking()
    got = mouth.lag(ap, ap)
    assert got["measured"] is True and got["lag_frames"] == 0 and got["corr"] > 0.9
    assert got["readable"] == 1.0


def test_a_half_read_face_is_still_unreadable_below_the_floor():
    ap = talking()
    ap[: int(72 * (1 - mouth.READABLE) + 1)] = np.nan
    assert mouth.lag(ap, talking())["measured"] is False


def test_the_voice_envelope_is_one_value_a_frame():
    sr, seconds = 24000, 3.0
    wav = np.random.default_rng(2).normal(0, 0.3, int(sr * seconds))
    env = mouth.voice_envelope(wav, sr, fps=24)
    assert env.shape == (72,) and abs(env.mean()) < 1e-6


def test_the_real_landmarker_is_never_downloaded(tmp_path):
    with pytest.raises(FileNotFoundError):
        mouth.facemesh(tmp_path / "face_landmarker.task")
