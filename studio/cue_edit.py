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

Two layers.  The sample layer (`slice_bars`, `splice`, `splice_out`,
`repeat_bars`, `hole`, `stop_at`, `section_gains`, `conform`) edits audio and
returns audio.  The grid layer (`bars_covering`, `keep_spans`, `conform_bars`,
`remove_bars`) is what steps 03 and 08 call: it runs the same edit AND returns
a `Recut` -- the `Metre` the cue now has, plus an `Edit` record per block --
so the plan is re-derived from a grid that agrees with the samples.  The grid
is DERIVED from the edit, never re-measured: an edit on downbeats moves every
later downbeat by exactly the seconds it removed, so re-measuring could only
add error.
"""
from __future__ import annotations

from typing import Iterable, Literal

import numpy as np
from pydantic import BaseModel, Field

from studio.cue_plan import CueSection
from studio.trailer_assemble import HARD_OUT_GATE
from studio.trailer_stage_spec import Metre, Slot

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

LANDS_WITHIN = 0.010
"""Seconds within which a time LANDS on a downbeat or a hit: a cut that moved
ZERO_WINDOW to a zero crossing still lands, and 10 ms is what the ear resolves
(the same figure as HIT_FADE, for the same reason)."""


class Edit(BaseModel):
    """One block of the edit: which bars of the source, and where in the
    output they land (`at`, seconds) or, for a removal, where the join is."""

    op: Literal["keep", "remove"]
    first_bar: int = Field(ge=0)
    last_bar: int = Field(ge=0)
    at: float = Field(ge=0.0)
    fade_s: float = Field(ge=0.0)


class Cut(BaseModel):
    """A removal between two measured times rather than two bar lines: what a
    cue measured as onsets (no downbeats) is cut by.  `at` is the join."""

    op: Literal["cut"] = "cut"
    start_s: float = Field(ge=0.0)
    end_s: float = Field(gt=0.0)
    at: float = Field(ge=0.0)
    fade_s: float = Field(ge=0.0)


class Recut(BaseModel):
    """What a grid-layer edit hands back beside the samples: the metre the cue
    now has, and the edits that made it."""

    metre: Metre
    edits: list[Edit | Cut] = Field(min_length=1)


def mid(samples: np.ndarray) -> np.ndarray:
    """The mono guide of a cue: the samples themselves, or the mean of the
    channels.  Every decision about WHERE to cut is taken on it, so a stereo
    cue is cut at one sample across both channels."""
    return samples if samples.ndim == 1 else samples.mean(axis=1)


def per_sample(gain: np.ndarray, samples: np.ndarray) -> np.ndarray:
    """A per-sample gain shaped to multiply `samples`, mono or channels."""
    return gain if samples.ndim == 1 else gain[:, None]


def zero_cross(samples: np.ndarray, at_sample: int, window: int) -> int:
    """The index nearest `at_sample` where the sign flips, within `window`
    samples; `at_sample` itself when there is none.  Ties go to the earlier
    crossing, so a cut prefers to fall before the transient, not into it."""
    lo, hi = max(1, at_sample - window), min(len(samples) - 1, at_sample + window)
    if hi <= lo:
        return at_sample
    signs = np.sign(mid(samples)[lo - 1:hi + 1])
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
    return indices_between(samples, rate, *bar_bounds(metre, first_bar, last_bar))


def indices_between(samples: np.ndarray, rate: int, start_s: float, end_s: float) -> tuple[int, int]:
    """Sample indices of two measured times, each moved to the nearest zero
    crossing of the mid."""
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
    overlap = (a[len(a) - n:] * per_sample(np.cos(theta), a)
               + b[:n] * per_sample(np.sin(theta), b))
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
    return (samples * per_sample(gain, samples)).astype(samples.dtype)


def stop_at(samples: np.ndarray, rate: int, at_s: float, tail_s: float) -> np.ndarray:
    """A hard out: the bed falls to nothing over HARD_OUT_GATE, done AT `at_s`,
    then `tail_s` of digital silence for the impact to land in."""
    at = int(round(at_s * rate))
    if at > len(samples):
        raise ValueError(f"a stop at {at_s}s lies past the cue")
    t = np.arange(at) / rate
    gate = np.clip((at_s - t) / HARD_OUT_GATE, 0.0, 1.0)
    tail = np.zeros((int(round(tail_s * rate)), *samples.shape[1:]), dtype=samples.dtype)
    return np.concatenate([(samples[:at] * per_sample(gate, samples)).astype(samples.dtype), tail])


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
    gain = gain_envelope(len(samples), rate, knots)
    return (samples * per_sample(gain, samples)).astype(samples.dtype)


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


# --- the grid layer ----------------------------------------------------------

def lands_on(t: float, marks: Iterable[float], tol: float = LANDS_WITHIN) -> bool:
    """Whether `t` sits within `tol` of any mark."""
    return any(abs(t - m) <= tol for m in marks)


def fade_at(metre: Metre, t: float, marks: Iterable[float] = ()) -> float:
    """The crossfade for a join at `t`: HIT_FADE when it lands on a measured hit
    or on a mark the caller names (a section start the plan cuts on), else
    half a beat."""
    return fade_for(metre, lands_on(t, [*metre.hits, *marks]))


def bar_at(metre: Metre, t: float) -> int:
    """Index of the bar whose downbeat `t` lands on."""
    for i, downbeat in enumerate(metre.downbeats):
        if abs(t - downbeat) <= LANDS_WITHIN:
            return i
    raise ValueError(f"{t}s is not on a downbeat of the cue")


def bars_covering(metre: Metre, start_s: float, end_s: float) -> tuple[int, int]:
    """The bars a span occupies, `start_s` on its first downbeat and `end_s`
    on the downbeat after its last -- or the cue's end, which closes the last
    bar.  A span is whole bars or it is not this module's to cut."""
    first = bar_at(metre, start_s)
    at_end = abs(end_s - metre.seconds) <= LANDS_WITHIN
    last = len(metre.downbeats) - 1 if at_end else bar_at(metre, end_s) - 1
    if last < first:
        raise ValueError(f"{start_s}-{end_s}s covers less than a bar")
    return first, last


def runs(bars: Iterable[int]) -> list[tuple[int, int]]:
    """Bar indices collapsed to inclusive contiguous ranges: `[0, 1, 4]` is
    `[(0, 1), (4, 4)]`.  How a plan's `keep_bars` becomes `conform`'s ranges."""
    out: list[tuple[int, int]] = []
    for bar in sorted(set(bars)):
        if out and bar == out[-1][1] + 1:
            out[-1] = (out[-1][0], bar)
        else:
            out.append((bar, bar))
    return out


def offsets_of(spans: list[tuple[float, float]]) -> list[float]:
    """Where each kept span begins in the output: the seconds kept before it."""
    out, at = [], 0.0
    for start, end in spans:
        out.append(at)
        at += end - start
    return out


def shifted(times: Iterable[float], spans: list[tuple[float, float]]) -> list[float]:
    """Each time inside a kept span, moved to where that span now sits; a time
    in dropped seconds is gone.  Spans are half-open, so the downbeat that
    CLOSES a kept span belongs to the bar after it and is dropped with it."""
    out = []
    for t in times:
        for (start, end), at in zip(spans, offsets_of(spans)):
            if start <= t < end:
                out.append(round(at + t - start, 4))
                break
    return sorted(out)


def kept_slots(slots: list[Slot], spans: list[tuple[float, float]]) -> list[Slot]:
    """Slots lying whole inside one kept span, moved with it; a slot the edit
    cuts through is gone, because a line cannot sit across a join."""
    out = []
    for slot in slots:
        for (start, end), at in zip(spans, offsets_of(spans)):
            if start <= slot.start and slot.end <= end:
                out.append(Slot(start=round(at + slot.start - start, 4),
                                end=round(at + slot.end - start, 4), made=slot.made))
                break
    return out


def keep_spans(metre: Metre, spans: list[tuple[float, float]]) -> Metre:
    """The metre of the cue made of `spans` (seconds, in output order) laid
    end to end: every measured time moved with its span, every dropped time
    gone, tempo and grid kind unchanged.  Re-validated, so an edit that broke
    the grid is refused here rather than read downstream."""
    spans = [(start, end) for start, end in spans if end > start]
    title = shifted([metre.title_hit], spans) if metre.title_hit is not None else []
    return Metre.model_validate({
        **metre.model_dump(),
        "seconds": round(sum(end - start for start, end in spans), 4),
        "beats": shifted(metre.beats, spans),
        "downbeats": shifted(metre.downbeats, spans),
        "hits": shifted(metre.hits, spans),
        "stopdowns": shifted(metre.stopdowns, spans),
        "phrase_starts": shifted(metre.phrase_starts, spans),
        "title_hit": title[0] if title else None,
        "slots": kept_slots(metre.slots, spans)})


def keep_edits(ranges: list[tuple[int, int]], spans: list[tuple[float, float]],
               fade_s: float) -> list[Edit]:
    """One `keep` per range, landed where its span sits in the output; the
    first block opens the cue and carries no fade."""
    return [Edit(op="keep", first_bar=first, last_bar=last, at=round(at, 4),
                 fade_s=0.0 if i == 0 else fade_s)
            for i, ((first, last), at) in enumerate(zip(ranges, offsets_of(spans)))]


def conform_bars(samples: np.ndarray, rate: int, metre: Metre, keep_bars: Iterable[int],
                 fade_s: float = HIT_FADE) -> tuple[np.ndarray, Recut]:
    """Row 56's call: the cue rebuilt from `keep_bars` (indices, a `range` or
    a list read off `CuePlan.sections` through `bars_covering`), and the metre
    the short now has, for `music_events` and `plan_of` to run on."""
    ranges = runs(keep_bars)
    out = conform(samples, rate, metre, ranges, fade_s)
    spans = [bar_bounds(metre, first, last) for first, last in ranges]
    return out, Recut(metre=keep_spans(metre, spans), edits=keep_edits(ranges, spans, fade_s))


def remove_bars(samples: np.ndarray, rate: int, metre: Metre, first_bar: int, last_bar: int,
                fade_s: float = HIT_FADE) -> tuple[np.ndarray, Recut]:
    """Row 53's call: a lost span's bars (`bars_covering`) spliced out, and
    the metre with every later time moved up by the bars removed -- the
    pre-roll before the first downbeat stays, as `splice_out` keeps it."""
    out = splice_out(samples, rate, metre, first_bar, last_bar, fade_s)
    start, end = bar_bounds(metre, first_bar, last_bar)
    kept = keep_spans(metre, [(0.0, start), (end, metre.seconds)])
    edit = Edit(op="remove", first_bar=first_bar, last_bar=last_bar, at=round(start, 4), fade_s=fade_s)
    return out, Recut(metre=kept, edits=[edit])


def remove_range(samples: np.ndarray, rate: int, metre: Metre, start_s: float, end_s: float,
                 fade_s: float | None = None) -> tuple[np.ndarray, Recut]:
    """A lost span cut out between two measured times -- the settle for a cue
    that measured as onsets, where `remove_bars` has no bar to name.  The
    fade is HIT_FADE when the join lands on a hit, else half a beat."""
    fade = fade_at(metre, start_s) if fade_s is None else fade_s
    start, end = indices_between(samples, rate, start_s, end_s)
    out = _land(samples, rate, samples[:start], end, len(samples), fade)
    kept = keep_spans(metre, [(0.0, start_s), (end_s, metre.seconds)])
    cut = Cut(start_s=round(start_s, 4), end_s=round(end_s, 4), at=round(start_s, 4), fade_s=fade)
    return out, Recut(metre=kept, edits=[cut])


def hole_bars(samples: np.ndarray, rate: int, metre: Metre, first_bar: int, last_bar: int,
              depth_db: float, return_s: float) -> np.ndarray:
    """The asked `hole` event: a dropout over whole bars, the music returning
    on the downbeat after `last_bar`."""
    start, end = bar_bounds(metre, first_bar, last_bar)
    return hole(samples, rate, start, end - start, depth_db, return_s)


def section_bounds(sections: list[CueSection]) -> list[tuple[float, float]]:
    """A plan's sections as the (start, end) bounds `section_gains` steps on."""
    return [(section.start, section.end) for section in sections]
