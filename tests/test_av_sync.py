"""The sync gate for an anchored take: the take's own track against the
input wav, as a lag in seconds (0 means the mouth is on our wav to the frame)."""
import numpy as np

from studio import av_sync


def burst(sr=24000, seconds=3.0, at=0.5, length=0.8, seed=0):
    rng = np.random.default_rng(seed)
    x = np.zeros(int(sr * seconds))
    x[int(sr * at):int(sr * (at + length))] = rng.normal(0, 0.3, int(sr * length))
    return x


def test_an_identical_track_has_zero_lag():
    x = burst()
    assert abs(av_sync.lag_seconds(x, x, 24000)) < 0.005


def test_a_delayed_copy_reports_the_delay():
    ref, late = burst(at=0.5), burst(at=0.8)
    assert abs(av_sync.lag_seconds(late, ref, 24000) - 0.3) < 0.01


def test_an_early_copy_reports_a_negative_lag():
    ref, early = burst(at=0.8), burst(at=0.5)
    assert abs(av_sync.lag_seconds(early, ref, 24000) + 0.3) < 0.01
