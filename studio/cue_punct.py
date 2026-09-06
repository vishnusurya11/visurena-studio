"""Trailer punctuation: the sub impact, the riser and the ceiling, synthesised.

A trailer's grammar is punctuation as much as music: a braam on the hit,
a riser that swells into the silence, an impact when the music returns,
one more under the title.  The song model provides these unreliably --
its hits fall where its own form puts them, not where the ask does -- so
the landmarks the ask names are punctuated HERE, deterministically, from
sine and noise, at the downbeats `cue_arc.arc` reports.  The bed is
trimmed BED_TRIM_DB to make room, and the sum is bent, not cut, at the
ceiling; step 08's mastering owns the true peak.
"""
from __future__ import annotations

import numpy as np

from studio.cue_ask import HOLE_BARS
from studio.cue_plan import CueAsk

IMPACT_SECONDS = 1.6
"""How long a sub impact rings; a cinematic boom is a second and a half."""

IMPACT_GAIN = 0.6
"""Peak of an impact on a hit or a return, against a bed trimmed BED_TRIM_DB."""

TITLE_GAIN = 1.0
"""The title impact is the loudest single event of the cue."""

RISER_BARS = 2
"""Bars a riser swells over into a hole: the phrase before the silence."""

RISER_GAIN = 0.5

BED_TRIM_DB = 3.0
"""The bed steps down this far under the punctuation, so the sum has room."""

KNEE = 0.85
"""Above this the sum is bent toward 1.0 -- a limiter's knee, near enough."""

SEED = 7
"""One seed for the noise: the same ask punctuates the same way every run."""


def impact(rate: int, seconds: float = IMPACT_SECONDS, f0: float = 70.0, f1: float = 32.0,
           gain: float = IMPACT_GAIN) -> np.ndarray:
    """A cinematic boom: a sine falling in pitch as it decays, with a click of
    low-passed noise on its front so the edge reads on small speakers."""
    rng = np.random.default_rng(SEED)
    t = np.arange(int(rate * seconds)) / rate
    freq = f1 + (f0 - f1) * np.exp(-t * 6.0)
    body = np.sin(2 * np.pi * np.cumsum(freq) / rate) * np.exp(-t * 2.2)
    click = np.convolve(rng.standard_normal(len(t)) * np.exp(-t * 60.0), np.ones(24) / 24, mode="same")
    out = body + 0.35 * click
    return (out / np.abs(out).max() * gain).astype(np.float32)


def riser(rate: int, seconds: float, gain: float = RISER_GAIN) -> np.ndarray:
    """A noise riser: brightening and swelling, ending exactly at its end."""
    rng = np.random.default_rng(SEED)
    t = np.arange(int(rate * seconds)) / rate
    noise = rng.standard_normal(len(t))
    alpha = 0.002 + 0.25 * (t / seconds) ** 2
    out, y = np.zeros_like(noise), 0.0
    for i in range(len(noise)):
        y += alpha[i] * (noise[i] - y)
        out[i] = y
    return (out * (t / seconds) ** 3 * gain).astype(np.float32)


def soft_knee(x: np.ndarray, knee: float = KNEE) -> np.ndarray:
    """Peaks above `knee` bent toward 1.0 by a tanh, the rest untouched."""
    over = np.abs(x) > knee
    y = np.array(x, dtype=np.float32, copy=True)
    y[over] = np.sign(x[over]) * (knee + (1 - knee) * np.tanh((np.abs(x[over]) - knee) / (1 - knee)))
    return y


def mix_at(bed: np.ndarray, rate: int, sound: np.ndarray, at_s: float) -> np.ndarray:
    """`sound` added into `bed` from `at_s`, cut at the bed's end, on every channel."""
    at = int(round(at_s * rate))
    end = min(len(bed), at + len(sound))
    if at < 0 or end <= at:
        return bed
    piece = sound[: end - at]
    bed[at:end] += piece if bed.ndim == 1 else piece[:, None]
    return bed


def landmarks(ask: CueAsk) -> tuple[list[int], list[int]]:
    """(bars that take an impact, bars a riser ends on): the hit, every
    hole's return; every hole's start."""
    holes = [e.bar for e in ask.events if e.kind == "hole"]
    hits = [e.bar for e in ask.events if e.kind == "hit"] + [b + HOLE_BARS for b in holes]
    return hits, holes


def punctuate(bed: np.ndarray, rate: int, downbeats: list[float], ask: CueAsk) -> np.ndarray:
    """The ask's landmarks punctuated on the arc: impacts on the hit, every
    hole's return and the title; a riser into every hole; the sum under the ceiling."""
    out = bed.astype(np.float32) * 10 ** (-BED_TRIM_DB / 20)
    hits, holes = landmarks(ask)
    for bar in hits:
        if bar < len(downbeats):
            out = mix_at(out, rate, impact(rate), downbeats[bar])
    for bar in holes:
        rise = riser(rate, RISER_BARS * ask.bar)
        out = mix_at(out, rate, rise, downbeats[bar] - len(rise) / rate)
    out = mix_at(out, rate, impact(rate, seconds=2.5, f0=60.0, f1=28.0, gain=TITLE_GAIN),
                 downbeats[ask.title_bar])
    return soft_knee(out)
