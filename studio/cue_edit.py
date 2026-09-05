"""Editing a rendered cue on its MEASURED bar lines: cut, splice, repeat,
hole, stop, staircase, conform.  Samples in, samples out; nothing here
decodes a file, runs ffmpeg or asks a model.

The brick is one rule: every edit lands on a measured downbeat and every join
is a crossfade whose overlap ENDS on that downbeat.  The bar before the join
carries the fade; the new bar's "one" is untouched.  Cut there, and the ear
has nothing to hear: the transient that arrives at the downbeat is the music's
own, and a summed equal-power crossfade holds the level across the overlap
(cos^2 + sin^2 = 1).  Everything below is that rule applied to one operation.

Bars are read from `Metre.downbeats`, never from the nominal `bar`: within one
seed bars drift 2-4 % (770301: 1.66 -> 4.18 -> 6.70 s), so a nominal grid walks
off the music inside eight bars.  The only exception is the last bar, which
has no downbeat after it and ends where the cue ends.

Nothing here stretches audio, and nothing will.  Time-stretching a bed by
more than about 3 % smears its transients, and 3 % buys nothing: eight bars
at 84 BPM stretch by a beat and a half, less than one dropped bar.  The
repo's other audio paths already hold this line (`trailer_dialogue` never
`atempo`s a line).  The plan moves the PICTURE to the music; when the music
must move, it moves by whole bars, on downbeats, through these functions.
"""
from __future__ import annotations

import numpy as np

from studio.trailer_assemble import HARD_OUT_GATE
from studio.trailer_stage_spec import Metre

ZERO_WINDOW = 0.005
"""FLAG.  Seconds either side of a downbeat a cut may move to find a zero
crossing: 0.7 % of a beat at 84 BPM, below the ~10 ms the ear resolves."""

HIT_FADE = 0.010
"""FLAG.  Crossfade seconds when the join lands on a hit; the transient masks
it.  Where texture continues the fade is half a beat (`fade_for`)."""

COMPAT_DB = 3.0
"""FLAG.  The most the two sides of a join may differ in RMS before the join
reads as a fader jump rather than the music continuing."""

GAIN_RAMP = 0.05
"""FLAG.  Default ramp at a section bound, ending on the bound.  The plan may
ask for a whole bar (`section_gains(..., ramp_s=metre.bar)`)."""

SECTION_GAIN_LIMIT = 3.0
"""FLAG.  dB a section may sit from unity.  +-3 dB steps read as arrangement;
more reads as a fader."""

TEMPO_TOLERANCE = 0.01
"""FLAG.  Relative BPM difference two seeds may have and still be joined."""


def zero_cross(samples: np.ndarray, at_sample: int, window: int) -> int:
    """The index nearest `at_sample` where the sign flips, within `window`
    samples; `at_sample` itself when there is none.  Ties go to the earlier
    crossing, so a cut prefers to fall before the transient, not into it."""
    lo, hi = max(1, at_sample - window), min(len(samples) - 1, at_sample + window)
    if hi <= lo:
        return at_sample
    signs = np.sign(samples[lo - 1:hi + 1])
    flips = np.flatnonzero(signs[1:] != signs[:-1]) + lo
    if len(flips) == 0:
        return at_sample
    return int(flips[np.argmin(np.abs(flips - at_sample) * 2 + (flips > at_sample))])


def bar_bounds(metre: Metre, first_bar: int, last_bar: int) -> tuple[float, float]:
    """Seconds of bars `first_bar..last_bar` (inclusive), read from the measured
    downbeats.  The last bar of the cue ends where the cue ends."""
    count = len(metre.downbeats)
    if not 0 <= first_bar <= last_bar < count:
        raise ValueError(f"bars {first_bar}..{last_bar} lie outside the cue's {count} bars")
    start = metre.downbeats[first_bar]
    end = metre.downbeats[last_bar + 1] if last_bar + 1 < count else metre.seconds
    return start, end


def cut_indices(samples: np.ndarray, rate: int, metre: Metre,
                first_bar: int, last_bar: int) -> tuple[int, int]:
    """Sample indices of a bar range, each moved to the nearest zero crossing."""
    start_s, end_s = bar_bounds(metre, first_bar, last_bar)
    window = int(round(ZERO_WINDOW * rate))
    start = zero_cross(samples, int(round(start_s * rate)), window)
    end = zero_cross(samples, min(int(round(end_s * rate)), len(samples)), window)
    return start, end


def slice_bars(samples: np.ndarray, rate: int, metre: Metre,
               first_bar: int, last_bar: int) -> np.ndarray:
    """Whole bars lifted from the cue, cut at zero crossings.  Its length is
    measured bars, so it keeps phase when landed on another downbeat."""
    start, end = cut_indices(samples, rate, metre, first_bar, last_bar)
    return samples[start:end]


def rms_db(samples: np.ndarray) -> float:
    """RMS level in dBFS; digital silence reads as -240 rather than -inf."""
    return float(20 * np.log10(np.sqrt(np.mean(samples.astype(np.float64) ** 2)) + 1e-12))


def compatible(a: np.ndarray, b: np.ndarray, rate: int, window_s: float) -> bool:
    """Whether `a`'s tail and `b`'s head sit within COMPAT_DB of each other
    over the join window -- the precondition for an equal-power crossfade to
    hold level rather than step."""
    n = max(1, int(round(window_s * rate)))
    return abs(rms_db(a[-n:]) - rms_db(b[:n])) <= COMPAT_DB


def compatible_tempo(a: Metre, b: Metre) -> bool:
    """Whether two seeds may be joined at all: tempo within TEMPO_TOLERANCE.
    Beyond it the fix would be stretching, and stretching is refused."""
    return abs(a.bpm - b.bpm) / a.bpm <= TEMPO_TOLERANCE


def fade_for(metre: Metre, on_hit: bool) -> float:
    """Crossfade seconds: half a beat where texture continues, HIT_FADE where
    the join lands on a hit."""
    return HIT_FADE if on_hit else metre.beat / 2


def splice(a: np.ndarray, b: np.ndarray, rate: int, fade_s: float) -> np.ndarray:
    """`a` into `b` through an equal-power crossfade over `fade_s`.

    The overlap is `a`'s last and `b`'s first `n` samples, so a caller who
    wants the join to END on a downbeat hands over `b` with `n` samples of
    pre-roll.  Refuses a join whose two sides differ in level.
    """
    n = int(round(fade_s * rate))
    if n > len(a) or n > len(b):
        raise ValueError(f"a {fade_s}s fade needs {n} samples on both sides")
    if not compatible(a, b, rate, fade_s):
        raise ValueError(f"levels differ by more than {COMPAT_DB} dB at the join")
    theta = np.linspace(0.0, np.pi / 2, n, endpoint=False)
    overlap = a[len(a) - n:] * np.cos(theta) + b[:n] * np.sin(theta)
    return np.concatenate([a[:len(a) - n], overlap, b[n:]]).astype(a.dtype)


def _land(samples: np.ndarray, rate: int, head: np.ndarray, at: int, end: int,
          fade_s: float) -> np.ndarray:
    """`head` spliced into `samples[at:end]` so the overlap ends at `at`: the
    pre-roll is the tail of whatever the cue plays before `at`."""
    n = min(int(round(fade_s * rate)), at)
    return splice(head, samples[at - n:end], rate, n / rate)


def splice_out(samples: np.ndarray, rate: int, metre: Metre, first_bar: int,
               last_bar: int, fade_s: float = HIT_FADE) -> np.ndarray:
    """Remove a bar range and rejoin on the bar line.  The cue shortens by
    exactly the removed bars and every later downbeat lands where the removed
    range began, so the grid after the cut is the grid before it.

    The join lands on a downbeat -- the cue's own transient -- so the default
    fade is HIT_FADE (settle, research doc section 7).
    """
    start, end = cut_indices(samples, rate, metre, first_bar, last_bar)
    return _land(samples, rate, samples[:start], end, len(samples), fade_s)


def repeat_bars(samples: np.ndarray, rate: int, metre: Metre, first_bar: int,
                last_bar: int, times: int, fade_s: float = HIT_FADE) -> np.ndarray:
    """The block `first_bar..last_bar` played `times` times in all, the extra
    copies spliced in after it; the rest of the cue follows unchanged.  Only
    for a flat plateau -- a repeated rise is a rise heard twice."""
    if times < 1:
        raise ValueError("a block plays at least once")
    start, end = cut_indices(samples, rate, metre, first_bar, last_bar)
    out = samples[:end]
    for _ in range(times - 1):
        out = _land(samples, rate, out, start, end, fade_s)
    return np.concatenate([out, samples[end:]])


def hole(samples: np.ndarray, rate: int, start_s: float, seconds: float,
         depth_db: float, return_s: float) -> np.ndarray:
    """A dropout: gate down to `depth_db` over HARD_OUT_GATE at `start_s`, hold,
    then an equal-power return over `return_s` that ENDS at `start_s + seconds`
    -- the downbeat the music comes back on."""
    floor = 10 ** (depth_db / 20)
    t = np.arange(len(samples)) / rate
    gate = np.clip((t - start_s) / HARD_OUT_GATE, 0.0, 1.0)
    back = np.clip((t - (start_s + seconds - return_s)) / return_s, 0.0, 1.0)
    rise = np.sin(back * np.pi / 2)
    gain = 1.0 - gate * (1.0 - floor) * (1.0 - rise)
    gain[t >= start_s + seconds] = 1.0
    return (samples * gain).astype(samples.dtype)


def stop_at(samples: np.ndarray, rate: int, at_s: float, tail_s: float) -> np.ndarray:
    """A hard out: the bed falls to nothing over HARD_OUT_GATE, done AT `at_s`,
    then `tail_s` of digital silence for the impact to land in."""
    at = int(round(at_s * rate))
    if at > len(samples):
        raise ValueError(f"a stop at {at_s}s lies past the cue")
    t = np.arange(at) / rate
    gate = np.clip((at_s - t) / HARD_OUT_GATE, 0.0, 1.0)
    tail = np.zeros(int(round(tail_s * rate)), dtype=samples.dtype)
    return np.concatenate([(samples[:at] * gate).astype(samples.dtype), tail])


def gain_envelope(length: int, rate: int, knots: list[tuple[float, float]]) -> np.ndarray:
    """Per-sample linear gain from (seconds, dB) knots, interpolated in dB so a
    ramp is the same size to the ear all the way along."""
    t = np.arange(length) / rate
    times, dbs = zip(*knots)
    return 10 ** (np.interp(t, times, dbs) / 20)


def section_gains(samples: np.ndarray, rate: int, bounds: list[tuple[float, float]],
                  gains_db: list[float], ramp_s: float = GAIN_RAMP) -> np.ndarray:
    """The staircase: one gain per section, each step a ramp ending on the
    section's first downbeat.  Steps past SECTION_GAIN_LIMIT are refused."""
    if len(bounds) != len(gains_db):
        raise ValueError("one gain per section")
    if any(abs(g) > SECTION_GAIN_LIMIT for g in gains_db):
        raise ValueError(f"a section gain past +-{SECTION_GAIN_LIMIT} dB reads as a fader")
    knots = [(0.0, gains_db[0])]
    for (start, _), before, after in zip(bounds[1:], gains_db, gains_db[1:]):
        knots += [(start - ramp_s, before), (start, after)]
    return (samples * gain_envelope(len(samples), rate, knots)).astype(samples.dtype)


def conform(samples: np.ndarray, rate: int, metre: Metre,
            keep_bars: list[tuple[int, int]], fade_s: float = HIT_FADE) -> np.ndarray:
    """The cue rebuilt from the kept bar ranges, in order, each landed on the
    downbeat of the next.  The ladder rung between more seeds and reauthor,
    and how the short is cut from the verified long cue."""
    if not keep_bars:
        raise ValueError("conform keeps at least one bar")
    first, *rest = keep_bars
    out = slice_bars(samples, rate, metre, *first)
    for first_bar, last_bar in rest:
        start, end = cut_indices(samples, rate, metre, first_bar, last_bar)
        out = _land(samples, rate, out, start, end, fade_s)
    return out
