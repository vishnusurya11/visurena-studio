"""The render's voicing matched to the measured spectrum of finished music.

MEASURED on every raw render of A Study in Scarlet (16 seeds, four tones):
against the mean long-term spectrum of commercial music (Elowsson &
Friberg 2017, Table 1) the model voices every cue the same way -- sub
50-100 Hz +2..+7 dB hot, the body 100-400 Hz 3..6 dB scooped, the low
mids 400-800 Hz +3..+6 boxy, the top 6.4 kHz up 9..15 dB dark.  Every
test plants a noise whose octave bands sit at chosen levels and reads
the result with the module's own spectrum.  Nothing decodes a file.
"""
from __future__ import annotations

import numpy as np
import pytest
from scipy.signal import fftconvolve, freqz

from studio import cue_voicing

RATE = 44100
EDGES = np.array(cue_voicing.EDGES, dtype=float)
CENTRES = np.sqrt(EDGES[:-1] * EDGES[1:])


def shaped(band_db: list[float], seconds: float = 8.0, seed: int = 3) -> np.ndarray:
    """White noise whose octave bands are set to `band_db` (per-bin level)."""
    rng = np.random.default_rng(seed)
    n = int(seconds * RATE)
    spec = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / RATE)
    band = np.clip(np.digitize(f, EDGES) - 1, 0, len(band_db) - 1)   # flat within each band
    gain = np.asarray(band_db, dtype=float)[band]
    return (np.fft.irfft(spec * 10 ** (gain / 20), n=n) * 0.05).astype(np.float32)


def test_reference_falls_from_100_hz_and_steepens_with_frequency():
    f = np.array([50.0, 100.0, 200.0, 400.0, 800.0, 1600.0, 3200.0, 6400.0, 12800.0])
    ref = cue_voicing.reference_db(f)
    assert ref[0] == ref[1] == pytest.approx(0.0)              # flat under the peak
    drops = -np.diff(ref[1:])                                   # each octave's drop
    assert np.all(drops > 0) and np.all(np.diff(drops) > 0)     # falling, ever steeper
    assert drops[3] == pytest.approx(5.6, abs=0.5)              # 800 Hz -> 1.6 kHz: Table 1's -5 dB/oct


def test_band_levels_reads_white_noise_as_flat_and_a_planted_bump():
    flat = cue_voicing.band_levels(*cue_voicing.spectrum(shaped([0.0] * len(CENTRES)), RATE))
    assert np.ptp(flat) < 1.5
    bump = [0.0] * len(CENTRES)
    bump[3] = 10.0
    bumped = cue_voicing.band_levels(*cue_voicing.spectrum(shaped(bump), RATE))
    assert bumped[3] - bumped[2] == pytest.approx(10.0, abs=1.5)


def test_voicing_gains_are_zero_on_the_reference_and_clipped_off_it():
    ref = cue_voicing.reference_db(CENTRES)
    assert np.allclose(cue_voicing.voicing_gains(ref + 7.0, CENTRES), 0.0, atol=1e-6)
    boxy = ref.copy()
    boxy[3] += 12.0                                              # 400-800 Hz 12 dB hot
    gains = cue_voicing.voicing_gains(boxy, CENTRES, limit=6.0)
    assert gains[3] == pytest.approx(-6.0, abs=0.01)             # asked for -12, limited
    assert np.all(np.abs(gains) <= 6.0)


def test_voicing_filter_has_the_asked_gain_at_each_band_centre():
    gains = np.array([2.0, -4.0, 0.0, -6.0, 3.0, 0.0, 6.0, 6.0, 6.0])
    h = cue_voicing.voicing_filter(gains, CENTRES, RATE)
    w, response = freqz(h, worN=CENTRES, fs=RATE)
    assert np.allclose(20 * np.log10(np.abs(response)), gains, atol=1.0)


def test_voice_pulls_a_boxy_dark_render_toward_the_reference():
    ref = cue_voicing.reference_db(CENTRES)
    rendered = ref + np.array([5.0, -4.0, -4.0, 5.0, 3.0, 0.0, -4.0, -10.0, -13.0])
    raw = shaped(list(rendered))
    voiced = cue_voicing.voice(raw, RATE)
    distance = lambda x: np.sqrt(np.mean((cue_voicing.voicing_gains(  # noqa: E731
        cue_voicing.band_levels(*cue_voicing.spectrum(x, RATE)), CENTRES, limit=99.0)) ** 2))
    assert len(voiced) == len(raw)
    assert distance(voiced) < distance(raw) * 0.5


def test_voice_keeps_a_stereo_cue_stereo_and_a_flat_reference_alone():
    ref = cue_voicing.reference_db(CENTRES)
    left = shaped(list(ref), seed=5)
    stereo = np.stack([left, 0.5 * left], axis=1)
    voiced = cue_voicing.voice(stereo, RATE)
    assert voiced.shape == stereo.shape
    assert np.allclose(voiced[:, 1], 0.5 * voiced[:, 0], atol=1e-6)
    assert 20 * np.log10(np.sqrt((voiced[:, 0] ** 2).mean()) / np.sqrt((left ** 2).mean())) == pytest.approx(0.0, abs=1.5)


def test_voice_drops_the_bands_a_low_rate_cannot_hold():
    """The tracker's 22.05 kHz cues end at 11 kHz: the 12.8-20 kHz band is empty there."""
    assert cue_voicing.edges_within(22050) == (50, 100, 200, 400, 800, 1600, 3200, 6400, 12800)
    assert cue_voicing.edges_within(44100) == cue_voicing.EDGES
    rng = np.random.default_rng(9)
    voiced = cue_voicing.voice((0.05 * rng.standard_normal(22050 * 4)).astype(np.float32), 22050)
    assert not np.isnan(voiced).any() and np.abs(voiced).max() > 0.01
