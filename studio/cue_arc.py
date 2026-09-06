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
from studio.beatmap import structural_impacts
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


def title_piece(samples: np.ndarray, rate: int, metre: Metre, bar: int, seconds: float) -> np.ndarray:
    """The impact bar and what follows it, `seconds` long, fading to black at the end."""
    last = min(len(metre.downbeats) - 1, bar + max(1, int(np.ceil(seconds / metre.bar))))
    piece = cue_edit.slice_bars(samples, rate, metre, bar, last)[: int(seconds * rate)].copy()
    fade = np.linspace(1.0, 0.0, min(len(piece), int(rate * min(1.5, seconds / 2))))
    piece[-len(fade):] *= cue_edit.per_sample(fade, piece)
    return piece


def staircase(samples: np.ndarray, rate: int, metre: Metre, ask: CueAsk,
              levels: np.ndarray) -> tuple[np.ndarray, list[float]]:
    """The bars up to the stop, quiet phrases first, holes gated, hard out on
    the stop bar with the asked silence after it; the downbeats so far."""
    stop, title = event_bars(ask, "stop")[0], ask.title_bar
    order = bar_order(levels, stop, usable=has_material(levels))
    body, downbeats = assemble(samples, rate, metre, ranges_of(order))
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
