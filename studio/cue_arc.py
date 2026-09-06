"""The editor's arc: the ask's staircase CUT from one render, on its bar lines.

MEASURED (BUILD row 60): five rounds of captions -- intensity adjectives,
a "Dynamics" sentence, descriptive section tags, a late [Chorus] -- moved
the song model's timbre (trailer > chamber on every seed) and never its
ORDER: every seed reaches its plateau by 20-30 % and stays there (climb
-0.6 dB over three seeds; the late-chorus sheet -4.4 and +3.5).  The
vendor's rule holds -- mood words are weak, tags command structure -- and
structure is not dynamics.  What the model reliably provides is MATERIAL
in both registers: intro bars at -27 to -37 dBFS, loud bars at -10 to -16,
same key, tempo and mastering.

So the arc is an EDIT.  Phrases sorted by measured level, quiet to loud,
fill the bars up to the stop; the ask's holes are gated on their bars, the
stop is a hard out on its bar, and the bar carrying the render's biggest
impact is landed on the title bar to decay alone.  The ask -- the spec the
cut map is verified against -- is delivered by construction, not by hope.
Measured on epic_cfg17-7005: climb -0.9 -> 11.0 dB, loudest 25 % -> 76 %.
`cue_edit.conform` refuses a join whose level steps by more than 3 dB
because a step reads as an edit; here the step on a downbeat IS the arc,
so `step_join` allows it and the join is only ever a downbeat.
"""
from __future__ import annotations

import numpy as np

from studio import cue_edit, music_events
from studio.cue_ask import HOLE_BARS
from studio.beatmap import WINDOW, structural_impacts
from studio.cue_plan import CueAsk
from studio.trailer_stage_spec import Metre

PHRASE_BARS = 4
"""Bars a phrase keeps together when the cue is re-ordered: the unit the
model composes in (a four-bar phrase is a musical sentence), so a join
lands between sentences, never inside one."""

STEP_FADE = 0.010
"""Crossfade seconds at a downbeat join; the downbeat's transient masks it
(the same figure as `cue_edit.HIT_FADE`, for the same reason)."""

HOLE_FLOOR_DB = -70.0
"""How far a hole gates down: digital black, the room a line is read over."""

HOLE_RETURN = 0.01
"""Seconds the music takes to return on the hole's downbeat: a switch, so
the return reads as a hit and not a fade-in."""

BLACK_DB = -60.0
"""A bar whose median level sits under this is black -- a stop's silence,
a tail -- and no phrase material: sorted by level it would open the cue.
The tracker's bar LINES are not the test any more: MEASURED (run 14),
raw-1001's first six tracked bars were 4.44 s at a 2.24 s bar (half time
over the drumless intro) and raw-1004 had 5 regular phrases of 11, so a
length rule threw away exactly the quiet material the intro needs."""


OCTAVE_BAND = 2 ** 0.5
"""A measured bar within this ratio of the asked bar is the render's own
bar; further off it is the tracker's tempo octave -- beats read at double
or half time -- and the bar lines are merged or split back to the ask.
MEASURED (run 13): raw-1001 tracked at 214 BPM against 100 asked; cut on
1.12 s bars the ask's 38 bars made a 43.7 s cue for a 91.2 s ask."""


def octave_steps(bar: float, target: float, band: float = OCTAVE_BAND) -> int:
    """Doublings (negative: halvings) that bring `bar` inside the band of `target`."""
    steps = 0
    while bar * 2 ** steps < target / band:
        steps += 1
    while bar * 2 ** steps > target * band:
        steps -= 1
    return steps


def split_bars(downbeats: list[float], seconds: float) -> list[float]:
    """Every bar cut at its midpoint, the last one ending at `seconds`."""
    ends = list(downbeats[1:]) + [seconds]
    return [t for start, end in zip(downbeats, ends) for t in (start, (start + end) / 2)]


def at_octave(metre: Metre, target: float) -> Metre:
    """The metre with its bar lines at the tempo octave nearest `target`;
    the metre itself when it is already inside the band."""
    steps = octave_steps(metre.bar, target)
    if steps == 0:
        return metre
    downbeats = list(metre.downbeats)
    for _ in range(steps):
        downbeats = downbeats[::2]
    for _ in range(-steps):
        downbeats = split_bars(downbeats, metre.seconds)
    beats = sorted(set(metre.beats) | set(downbeats))
    return metre.model_copy(update={"bar": metre.bar * 2 ** steps, "bpm": metre.bpm / 2 ** steps,
                                    "downbeats": downbeats, "beats": beats})


def bar_levels(metre: Metre, times: np.ndarray, db: np.ndarray) -> np.ndarray:
    """Median dBFS of every measured bar; a bar with no window reads as black."""
    ends = list(metre.downbeats[1:]) + [metre.seconds]
    out = []
    for start, end in zip(metre.downbeats, ends):
        inside = (times >= start) & (times < end)
        out.append(float(np.median(db[inside])) if inside.any() else HOLE_FLOOR_DB)
    return np.array(out)


def has_material(levels: np.ndarray, floor: float = BLACK_DB) -> np.ndarray:
    """Which measured bars hold sound: the phrase material."""
    return np.asarray(levels) > floor


def phrases_of(count: int, phrase: int = PHRASE_BARS) -> list[tuple[int, int]]:
    """Whole phrases of `phrase` bars over `count` bars; a trailing part is dropped."""
    return [(i, i + phrase - 1) for i in range(0, count - phrase + 1, phrase)]


def ascending(levels: np.ndarray, phrases: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """The phrases quiet to loud by mean level, ties in cue order."""
    return sorted(phrases, key=lambda p: float(levels[p[0]:p[1] + 1].mean()))


def bar_order(levels: np.ndarray, bars: int, phrase: int = PHRASE_BARS,
              usable: np.ndarray | None = None) -> list[int]:
    """Exactly `bars` source bars, quiet phrases first; when the render is
    short the loudest phrase plays again, as a climax does, and when it is
    long the middle goes (`cut_middle`).  A phrase with a bar not `usable`
    (see `has_material`) is left out."""
    phrases = [p for p in phrases_of(len(levels), phrase)
               if usable is None or usable[p[0]:p[1] + 1].all()]
    phrases = ascending(levels, phrases)
    if not phrases:
        raise ValueError(f"{len(levels)} bars is less than one {phrase}-bar phrase")
    order = [b for first, last in phrases for b in range(first, last + 1)]
    while len(order) < bars:
        order += list(range(phrases[-1][0], phrases[-1][1] + 1))
    return cut_middle(order, bars)


def cut_middle(order: list[int], bars: int) -> list[int]:
    """`order` shortened to `bars` out of its middle, so the quiet opening
    and the climax both stay.  MEASURED (raw-1001, v4): cut from the end,
    34 of 36 bars lost the loudest phrase's -13 and -12 dB bars before the
    stop; cut from the start, a 16-bar render loses its whole intro."""
    excess = len(order) - bars
    mid = (len(order) - excess) // 2
    return order[:mid] + order[mid + excess:]


def ranges_of(order: list[int]) -> list[tuple[int, int]]:
    """Consecutive source bars folded into one range, so a phrase is one slice."""
    ranges = [[order[0], order[0]]]
    for bar in order[1:]:
        if bar == ranges[-1][1] + 1:
            ranges[-1][1] = bar
        else:
            ranges.append([bar, bar])
    return [(a, b) for a, b in ranges]


def step_join(a: np.ndarray, b: np.ndarray, rate: int, fade_s: float = STEP_FADE) -> np.ndarray:
    """`b` landed after `a` over an equal-power crossfade of `fade_s`; the
    level may step, because the join is a downbeat and the step is the arc."""
    n = min(int(rate * fade_s), len(a), len(b))
    ramp = np.linspace(0.0, np.pi / 2, n)
    mix = a[-n:] * cue_edit.per_sample(np.cos(ramp), a) + b[:n] * cue_edit.per_sample(np.sin(ramp), b)
    return np.concatenate([a[:-n], mix, b[n:]])


def assemble(samples: np.ndarray, rate: int, metre: Metre,
             ranges: list[tuple[int, int]]) -> tuple[np.ndarray, list[float]]:
    """The ranges in order, each cut from its first downbeat for its count
    of bars at the cue's bar and landed on the next downbeat; the downbeats
    of the result, uniform by construction.  The tracker's lines wander
    (half time over a drumless intro, a downbeat lost in a breakdown); the
    cue's bar does not, so the lines only say where a phrase starts."""
    out, downbeats, at = None, [], 0.0
    for first, last in ranges:
        bars = last - first + 1
        start = float(metre.downbeats[first])
        a, b = cue_edit.indices_between(samples, rate, start, start + bars * metre.bar)
        piece = samples[a:b]
        downbeats += [at + i * metre.bar for i in range(bars)]
        out = piece if out is None else step_join(out, piece, rate)
        at = len(out) / rate
    return out, downbeats


def hit_bar(metre: Metre, times: np.ndarray, db: np.ndarray) -> int:
    """The bar holding the render's biggest impact; the first bar when it has none."""
    hits = structural_impacts(times, db, count=1)
    if not hits:
        return 0
    return max(0, int(np.searchsorted(metre.downbeats, hits[0], side="right") - 1))


def event_bars(ask: CueAsk, kind: str) -> list[int]:
    return [e.bar for e in ask.events if e.kind == kind]


def gate_holes(out: np.ndarray, rate: int, downbeats: list[float], ask: CueAsk) -> np.ndarray:
    """Every asked hole gated to black for HOLE_BARS, back on its downbeat."""
    for bar in event_bars(ask, "hole"):
        end = downbeats[bar + HOLE_BARS] if bar + HOLE_BARS < len(downbeats) else len(out) / rate
        out = cue_edit.hole(out, rate, downbeats[bar], end - downbeats[bar], HOLE_FLOOR_DB, HOLE_RETURN)
    return out


RING_DB = -50.0
"""Where the title's ring-out has reached: black under the card.  MEASURED
(run 16, cue-1001): with a 1.5 s fade at the very end, the four bars after
the hit read -17 -24 -25 -28 dB -- the render carrying on under the card,
and the stop term false on its drum strokes."""

RING_BARS = 1.0
"""How long the render's material takes to ring out after the title hit,
in bars, held for one beat first.  MEASURED (arc 7, seeds 1001/1002/1004):
held a whole bar and rung out over three, the material's strokes in the
ring's first bar read -33 dB against a -17 dB hit and `stops_dead` was
false on every seed.  The decay under the card is the title impact's own
(`cue_punct`, 2.5 s); the render only has to get out of its way."""


def ring_out(length: int, hold: int, ring: int, floor_db: float = RING_DB) -> np.ndarray:
    """Unity for `hold` samples, a straight line in dB to `floor_db` over
    `ring` samples, the floor after."""
    hold, ring = min(hold, length), max(ring, 1)
    db = np.concatenate([np.zeros(hold), np.linspace(0.0, floor_db, ring), np.full(length, floor_db)])
    return 10 ** (db[:length] / 20)


def title_piece(samples: np.ndarray, rate: int, metre: Metre, bar: int, seconds: float) -> np.ndarray:
    """The impact beat at level and what follows it ringing out: impact, decay, black."""
    last = min(len(metre.downbeats) - 1, bar + max(1, int(np.ceil(seconds / metre.bar))))
    piece = cue_edit.slice_bars(samples, rate, metre, bar, last)[: int(seconds * rate)].copy()
    gain = ring_out(len(piece), int(metre.bar / 4 * rate), int(RING_BARS * metre.bar * rate))
    return (piece * cue_edit.per_sample(gain, piece)).astype(piece.dtype)


RIDE_DB = {"low": (-26.0, -26.0), "mid": (-18.0, -14.0), "high": (-14.0, -12.0)}
"""Where each section's bars are RIDDEN to, dBFS at the section's first and
last bar: low held, a step up at the hit, a climb through mid, high held to
the stop.  MEASURED (run 16, cue-1001): the render came back mastered flat
-- phrase means -24 -24 -17 -23 -18 -18 -25 -23 -26, a 9 dB range end to
end -- so the staircase the ORDER built was 9 dB tall where a trailer's is
15-20.  The level is the ask's to write, not the render's to offer.  High
still climbs its last decibel: held flat, the loudest five seconds sat at
the section's first bar (70% of the cue, MEASURED arc 7 seed 1001) and the
climb term wants them late, in LOUDEST_BAND."""

RIDE_MAX = 12.0
"""The most a bar is moved, either way: past this the noise floor of a quiet
bar comes up with it, or a loud bar is left with no transient."""


def ride_targets(ask: CueAsk, bars: int, stop: int | None = None) -> np.ndarray:
    """The level asked of every bar, interpolated between each section's
    ends; a section the stop falls in finishes its climb on the bar before it."""
    xs, ys = [], []
    for s in ask.sections:
        end = s.bar + s.bars - 1
        xs += [s.bar, min(end, stop - 1) if stop is not None and s.bar < stop else end]
        ys += list(RIDE_DB[s.level])
    return np.interp(np.arange(bars), xs, ys)


def ride_gains(levels: np.ndarray, targets: np.ndarray, usable: np.ndarray,
               limit: float = RIDE_MAX) -> np.ndarray:
    """dB per bar that takes each usable bar to its target, within the limit."""
    gains = np.clip(targets - levels, -limit, limit)
    return np.where(usable, gains, 0.0)


def body_levels(body: np.ndarray, rate: int, downbeats: list[float], bar: float) -> np.ndarray:
    """Median dBFS of every bar of an assembled body, read on its own uniform
    lines.  MEASURED (run 17, cue-1001): gains read off the tracker's bars of
    the RENDER (lines 3.02 s apart over a 2.24 s bar) moved bars `assemble`
    had cut from elsewhere -- -17 -15 -13 dB material filed as -27 -26 -22,
    one bar left at -40 for a -26 target.  What is ridden is measured after
    it is cut."""
    mono = body if body.ndim == 1 else body.mean(axis=1)
    width = int(rate * WINDOW)
    count = len(mono) // width
    rms = np.sqrt((mono[:count * width].reshape(count, width) ** 2).mean(axis=1))
    times, db = np.arange(count) * WINDOW, 20 * np.log10(np.maximum(rms, 1e-6))
    return np.array([float(np.median(db[(times >= d) & (times < d + bar)])) for d in downbeats])


def ride(samples: np.ndarray, rate: int, downbeats: list[float], gains_db: np.ndarray) -> np.ndarray:
    """The gains applied as one envelope, whole at each bar's centre and
    sliding between centres, so no bar line carries a step."""
    half = (downbeats[1] - downbeats[0]) / 2 if len(downbeats) > 1 else len(samples) / rate / 2
    centres = np.asarray(downbeats[:len(gains_db)]) + half
    gain = np.interp(np.arange(len(samples)) / rate, centres, gains_db)
    gain = gain[:, None] if samples.ndim == 2 else gain
    return (samples * 10 ** (gain / 20)).astype(samples.dtype)


def staircase(samples: np.ndarray, rate: int, metre: Metre, ask: CueAsk,
              levels: np.ndarray) -> tuple[np.ndarray, list[float]]:
    """The bars up to the stop, quiet phrases first, ridden to the asked
    levels, holes gated, hard out on the stop bar with the asked silence
    after it; the downbeats so far."""
    stop, title = event_bars(ask, "stop")[0], ask.title_bar
    order = bar_order(levels, stop, usable=has_material(levels))
    body, downbeats = assemble(samples, rate, metre, ranges_of(order))
    now = body_levels(body, rate, downbeats, metre.bar)
    body = ride(body, rate, downbeats, ride_gains(now, ride_targets(ask, ask.bars, stop)[:stop], has_material(now)))
    body = gate_holes(body, rate, downbeats, ask)
    body = cue_edit.stop_at(body, rate, len(body) / rate, (title - stop) * ask.bar)
    downbeats += [downbeats[-1] + (i + 1) * ask.bar for i in range(title - stop)]
    return body, downbeats


MAP_KINDS = {"pulse_in": "lift", "hit": "hit", "title_hit": "hit", "hole": "dropout", "stop": "dropout"}
"""Each asked event as the cut map names it."""


def event_end(ask: CueAsk, kind: str, bar: int, downbeats: list[float]) -> float | None:
    """Where an asked dropout ends: a hole after HOLE_BARS, the stop at the title."""
    if kind == "stop":
        return float(downbeats[ask.title_bar])
    if kind == "hole":
        return float(downbeats[bar]) + HOLE_BARS * ask.bar
    return None


def events_of(ask: CueAsk, downbeats: list[float]) -> list[dict]:
    """The ask's events on the arc's own bar lines, in the cut map's kinds,
    witnessed by the arc: what was cut is what the map is verified against."""
    return [music_events.event(downbeats[a.bar], MAP_KINDS[a.kind], f"arc:{a.kind}",
                               end=event_end(ask, a.kind, a.bar, downbeats))
            for a in ask.events]


def grid_of(downbeats: list[float], bar: float) -> tuple[list[float], list[float]]:
    """The arc's grid as a tracker would report it: four beats laid on every
    bar line, so `beatmap.metre` reads the cue on the lines it was cut on."""
    beats = [round(d + i * bar / 4, 4) for d in downbeats for i in range(4)]
    return beats, [float(d) for d in downbeats]


def arc(samples: np.ndarray, rate: int, metre: Metre, ask: CueAsk,
        times: np.ndarray, db: np.ndarray) -> tuple[np.ndarray, list[float]]:
    """The ask cut from the render: (samples, downbeats of every asked bar).
    `times`, `db` are the render's envelope, the instrument the levels and
    the impact are read with."""
    body, downbeats = staircase(samples, rate, metre, ask, bar_levels(metre, times, db))
    after = ask.bars - ask.title_bar
    tail = title_piece(samples, rate, metre, hit_bar(metre, times, db), after * ask.bar)
    downbeats += [downbeats[-1] + (i + 1) * ask.bar for i in range(after)]
    return np.concatenate([body, tail]).astype(samples.dtype), downbeats
