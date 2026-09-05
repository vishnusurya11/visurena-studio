"""The ask rendered as a click track: the fixture the verifier is proved on.

Every landmark the ask names -- pulse in, holes, hit, stop, title hit -- is
placed in the audio bar for bar, so `cue_ask.verify` is tested against
audio whose events are known to the sample.  Test-only: nothing in `studio`
imports this.
"""
from __future__ import annotations

import numpy as np

from studio.beatmap import RATE
from studio.cue_ask import HOLE_BARS, bar_time
from studio.cue_plan import CueAsk
from test_metre import click_track

LEVEL_GAIN = {"low": 0.1, "mid": 0.3, "high": 1.0}
"""-20, -10.5 and 0 dB: steps of about ten dB, well over a lift's six."""
DRONE = 0.03
"""A held low note under everything until the stop, so the intro is audible
and pulse-free; far enough under a click that every beat is an onset."""
BURST = 0.3
"""Seconds a hit's burst takes to decay to a thirtieth."""


def synth_from_ask(ask: CueAsk, rate: int = RATE) -> np.ndarray:
    """A click track that does what the ask says, bar for bar."""
    count = int(ask.seconds * rate)
    clicks, _, _ = click_track(ask.bpm, seconds=ask.seconds + 0.5, rate=rate)
    clicks = clicks[int(0.5 * rate):][:count]
    t = np.arange(count) / rate
    gains = gains_of(ask, count, rate)
    drone = DRONE * np.sin(2 * np.pi * 110.0 * t) * gains
    pulse = clicks * gains * (t >= bar_time(ask, event_bar(ask, "pulse_in")))
    out = (pulse + drone) * gate_of(ask, count, rate)
    return (out + hit_of(ask, count, rate)).astype(np.float32)


def event_bar(ask: CueAsk, kind: str) -> int:
    """The bar of the one event of this kind."""
    return next(e.bar for e in ask.events if e.kind == kind)


def gains_of(ask: CueAsk, count: int, rate: int) -> np.ndarray:
    """The section's level gain at every sample, before the pulse and after."""
    gains = np.zeros(count, dtype=np.float32)
    for section in ask.sections:
        start = int(section.bar * ask.bar * rate)
        end = min(count, int((section.bar + section.bars) * ask.bar * rate))
        gains[start:end] = LEVEL_GAIN[section.level]
    return gains


def gate_of(ask: CueAsk, count: int, rate: int) -> np.ndarray:
    """Ones, with every hole and everything after the stop at zero."""
    gate = np.ones(count, dtype=np.float32)
    for event in ask.events:
        if event.kind == "hole":
            start = int(event.bar * ask.bar * rate)
            gate[start:int((event.bar + HOLE_BARS) * ask.bar * rate)] = 0.0
    gate[int(event_bar(ask, "stop") * ask.bar * rate):] = 0.0
    return gate


def hit_of(ask: CueAsk, count: int, rate: int) -> np.ndarray:
    """A burst at the hit, and the title hit with the tail decaying to the end."""
    out = np.zeros(count, dtype=np.float32)
    t = np.arange(count) / rate
    for kind in ("hit", "title_hit"):
        at = event_bar(ask, kind) * ask.bar
        tau = BURST / 3.4 if kind == "hit" else max(BURST, (ask.seconds - at) / 4.0)
        after = t >= at
        out[after] += (np.exp(-(t[after] - at) / tau) * np.sin(2 * np.pi * 55.0 * (t[after] - at))
                       ).astype(np.float32)
    return out
