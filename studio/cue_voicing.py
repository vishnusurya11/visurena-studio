"""The render's voicing matched to the spectrum of finished music.

Nothing the arc does to LEVEL can fix a cue whose SPECTRUM is wrong, and
the song model voices every render the same wrong way.  MEASURED on the
sixteen raw renders of A Study in Scarlet against the mean long-term
spectrum of commercial music: sub 50-100 Hz +2..+7 dB hot, the body
100-400 Hz 3..6 dB scooped, the low mids 400-800 Hz +3..+6 dB boxy, the
top from 6.4 kHz 9..15 dB dark -- a small, hollow, dull sound where the
ask said huge.  So each render's octave bands are measured, the distance
from the reference shape is taken (level is the ride's business, so the
low bands' mean is the anchor) and a linear-phase filter moves each band
toward the reference, at most LIMIT_DB.

The reference: Elowsson & Friberg, "Long-term Average Spectrum in Popular
Music and its Relation to the Level of the Percussion", AES 142 (2017),
Table 1 -- the mean spectrum's slope in dB/octave at six centre
frequencies, in line with Pestana et al.'s 5 dB/octave over 100 Hz-4 kHz.
"""
from __future__ import annotations

import numpy as np
from scipy.signal import fftconvolve

SLOPES = {200.0: -2.350, 400.0: -3.668, 800.0: -4.985, 1600.0: -6.303, 3200.0: -7.621, 6400.0: -8.938}
"""dB per octave of the mean spectrum at each centre (Table 1); the slope
is linear in log frequency, so the level is its integral."""

PEAK_HZ = 100.0
"""The mean spectrum rises to about 100 Hz and falls from there."""

EDGES = (50, 100, 200, 400, 800, 1600, 3200, 6400, 12800, 20000)
"""Octave bands; the first five, up to 1.6 kHz, anchor the level."""

ANCHOR_BANDS = 6

LIMIT_DB = 6.0
"""The most any band moves: a cut takes nothing away that was there,
a boost raises whatever the model left in the band, hiss included."""

WINDOW = 8192
TAPS = 4095


def reference_db(freqs: np.ndarray) -> np.ndarray:
    """The mean spectrum's level at `freqs` relative to PEAK_HZ, flat below it."""
    octaves = np.log2(np.array(list(SLOPES)) / PEAK_HZ)
    per_octave, at_peak = np.polyfit(octaves, np.array(list(SLOPES.values())), 1)
    x = np.log2(np.maximum(np.asarray(freqs, dtype=float), PEAK_HZ) / PEAK_HZ)
    return at_peak * x + 0.5 * per_octave * x ** 2


def spectrum(samples: np.ndarray, rate: int, window: int = WINDOW) -> tuple[np.ndarray, np.ndarray]:
    """(frequencies, dB relative to the loudest bin): the mean power spectrum
    of half-overlapping Hann windows over the whole cue, mono."""
    mono = samples.mean(axis=1) if samples.ndim == 2 else samples
    taper = np.hanning(window)
    power = np.zeros(window // 2 + 1)
    for start in range(0, len(mono) - window, window // 2):
        power += np.abs(np.fft.rfft(mono[start:start + window] * taper)) ** 2
    return np.fft.rfftfreq(window, 1 / rate), 10 * np.log10(power / power.max() + 1e-15)


def band_levels(freqs: np.ndarray, db: np.ndarray, edges: tuple = EDGES) -> np.ndarray:
    """Each octave band's mean per-bin level."""
    return np.array([db[(freqs >= lo) & (freqs < hi)].mean() for lo, hi in zip(edges[:-1], edges[1:])])


def centres_of(edges: tuple = EDGES) -> np.ndarray:
    return np.sqrt(np.array(edges[:-1], dtype=float) * np.array(edges[1:], dtype=float))


def edges_within(rate: int, edges: tuple = EDGES) -> tuple:
    """The band edges a cue at `rate` can hold: bands starting under Nyquist."""
    return tuple(edge for i, edge in enumerate(edges) if i == 0 or edges[i - 1] < rate / 2)


def voicing_gains(levels: np.ndarray, centres: np.ndarray, limit: float = LIMIT_DB,
                  anchor: int = ANCHOR_BANDS) -> np.ndarray:
    """Per band, the dB to the reference SHAPE -- the anchor bands' mean
    difference is level, so it is taken out -- within +/-`limit`."""
    diff = reference_db(centres) - np.asarray(levels, dtype=float)
    return np.clip(diff - diff[:anchor].mean(), -limit, limit)


def voicing_filter(gains: np.ndarray, centres: np.ndarray, rate: int, taps: int = TAPS) -> np.ndarray:
    """A linear-phase FIR with `gains` dB at `centres`, interpolated on log
    frequency and held flat beyond the outermost centres."""
    freqs = np.fft.rfftfreq(taps, 1 / rate)
    curve = np.interp(np.log2(np.maximum(freqs, 1.0)), np.log2(centres), gains)
    kernel = np.fft.irfft(10 ** (curve / 20), n=taps)
    return np.roll(kernel, taps // 2) * np.hanning(taps)


def voice(samples: np.ndarray, rate: int, limit: float = LIMIT_DB) -> np.ndarray:
    """The cue with each octave band moved toward the reference shape."""
    edges = edges_within(rate)
    centres = centres_of(edges)
    gains = voicing_gains(band_levels(*spectrum(samples, rate), edges), centres, limit)
    kernel = voicing_filter(gains, centres, rate)
    if samples.ndim == 2:
        return np.stack([fftconvolve(samples[:, c], kernel, mode="same") for c in range(samples.shape[1])],
                        axis=1).astype(np.float32)
    return fftconvolve(samples, kernel, mode="same").astype(np.float32)
