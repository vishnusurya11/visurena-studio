"""Turning a measured cue into a shot list.

The rule the whole module serves: SHOT LENGTHS MUST VARY, and they must vary
in the shape the corpus shows -- open around 1.5s, breathe at a third, tighten
to about 0.55s at 85-90%, then hold the title for ~3s.  Uniform shot lengths
are the single most-named amateur tell, and they are what a generated pipeline
produces by default, because the model hands back clips of one fixed size.

Cuts are placed by walking the arc and SNAPPING to the nearest musical onset
when one is close enough.  Snapping is what puts picture and music together;
the arc is what stops every cut landing on every beat, which Lieu warns gets
"repetitive very quickly (and even nauseating)".
"""
from __future__ import annotations

from studio.trailer_cut import FINAL_HOLD, target_length

SNAP_TOLERANCE = 0.30
"""How far a cut will move to reach a musical onset.  Beyond this the arc
wins, because a cut dragged a long way to hit a beat stops serving the shot."""

LITERARY_STRETCH = 2.5
"""The corpus arc is measured on horror trailers -- the fastest-cutting kind.
A canonical text has no spoiler to protect, so its trailer sells tone and
world rather than withheld plot, and Woollen's register holds shots far
longer (his Birdman teaser keeps a single 32-second take).  Stretching the
arc keeps its SHAPE -- the variety and the late acceleration -- while cutting
the shot count to something a generated pipeline can actually cover."""

MAX_SHOT = 4.0
"""No shot may run longer than this, wherever the onsets happen to fall.

`cut_points` takes the onset NEAREST the arc's next position, unconditionally,
which is right when the music is dense and wrong when it is not.  The chosen
Scarlet cue has ONE onset in its entire eighth decile -- 81.4s to 91.6s -- and
the corpus arc asks for its fastest cutting at exactly 85-90%.  With nothing
near to land on, one shot stretched to 7.42 seconds at the climax: a static
bearded man held for a quarter of the trailer's final third.

The real fix is upstream -- the cue should have been asked for density there,
and refused for arriving without it.  This is the floor under that.
"""

MIN_SHOT = 0.4
"""Below this a shot reads as a flash frame rather than an image."""


def snap(when: float, grid: list[float], tolerance: float = SNAP_TOLERANCE) -> float:
    """Move a cut onto a musical onset if one is within tolerance."""
    if not grid:
        return when
    nearest = min(grid, key=lambda point: abs(point - when))
    return nearest if abs(nearest - when) <= tolerance else when


def quantise(seconds: float, fps: int = 24) -> float:
    """Round a duration to a whole number of frames.

    `extract` passes `-t` to ffmpeg, which cannot render a fraction of a frame.
    MEASURED, not assumed: it keeps every frame whose timestamp is below t, so
    the rendered count is `ceil(t * fps)` and a fractional duration rounds the
    picture UP -- 1.35s asks for 32.4 frames and gets 33, which is 1.375s.
    (An earlier note here claimed the opposite, that -t truncates downward.  It
    does not; the drift was real but its sign was guessed, and the fix that
    followed from the guess added a frame instead of saving one.)

    Every rounding is under a frame, and thirty-three of them accumulated to
    **1.28 seconds** between the planned picture and the delivered one, so the
    title card cut in early and the cue's braam landed 5.13s into it instead of
    3.85s.  Planning in frames means the plan and the file agree by
    construction, whichever way the renderer would have rounded.
    """
    # No minimum here.  This quantises a TIMESTAMP, and clamping it to one
    # frame made the cut start at 0.042s instead of 0.0.  The one-frame floor
    # belongs to durations, and MIN_SHOT already enforces it.
    return max(0, round(seconds * fps)) / fps


def cut_points(duration: float, grid: list[float], start: float = 0.0,
               stretch: float = LITERARY_STRETCH, fps: int = 24) -> list[float]:
    """Shot boundaries CHOSEN FROM the musical grid, paced by the arc.

    The previous version walked the arc and snapped to an onset only if one
    happened to lie within 0.3s.  With 20 onsets over 100s that is a hit rate
    of about 12%, and measured on the shipped cut it was **2 of 33 = 6%**.  The
    arc was the timeline and the music was decoration, which is the opposite of
    what this module claims to do.

    Now the arc proposes and the grid disposes: for each step we take the onset
    NEAREST the arc's next position, unconditionally.  The music therefore owns
    every cut, and the arc only decides which onset.
    """
    usable = [g for g in grid if start < g < duration]
    points = [quantise(start, fps)]
    while True:
        position = (points[-1] - start) / max(duration - start, 1e-6)
        nominal = points[-1] + target_length(position) * stretch
        if nominal >= duration - MIN_SHOT:
            break
        ahead = [g for g in usable if g > points[-1] + MIN_SHOT]
        ceiling = points[-1] + MAX_SHOT
        near = [g for g in ahead if g <= ceiling] or ahead
        landed = min(near, key=lambda g: abs(g - nominal)) if near else nominal
        if landed <= points[-1] + MIN_SHOT:
            landed = points[-1] + target_length(position) * stretch
        landed = min(landed, ceiling)
        points.append(quantise(landed, fps))
    if duration - points[-1] < MIN_SHOT and len(points) > 1:
        points.pop()
    points.append(quantise(duration, fps))
    return points


def lengths_of(points: list[float], fps: int = 24) -> list[float]:
    """Shot lengths, in whole frames.

    `round(b - a, 3)` looked harmless and was not.  The difference of two
    frame-aligned points is itself frame-aligned, and three decimals cannot
    hold it: 53 frames is 2.20833...s, which rounds to 2.208.  That particular
    value still renders 53 (see `frames_arg` for the measured rule), but the
    plan is now carrying a number that is not a frame count, and every consumer
    of it has to guess which way the renderer will go.  Returning frames means
    nobody guesses.
    """
    return [round((b - a) * fps) / fps for a, b in zip(points, points[1:])]


# --- the beat walk (research trailer-music-structure.md section 5) ---------

EPS = 1e-6
BEATS_BY_POSITION: list[tuple[float, tuple[float, ...]]] = [
    (0.30, (2, 4, 6, 8)), (0.80, (1, 2, 3, 4)), (0.92, (0.5, 1, 2)), (1.01, (1, 2, 4)),
]
"""Whole-beat shot lengths the arc may choose from, by position: long
phrases to open, single beats through the middle, half-beats at the climax."""
HOLD_POSITION = 0.15
"""Without a title moment the one hold goes here, where the corpus breathes."""


def max_shot(bar: float, fps: int = 24) -> float:
    """The cap: 4 s or a bar and a quarter, whichever is longer, in whole frames.

    A fixed 4 s cap at 60 BPM allows exactly one bar, so every long shot is
    a bar and the cut turns uniform; a bar and a quarter leaves room to vary.
    The constant `MAX_SHOT` remains the floor of the cap.
    """
    return -(-max(MAX_SHOT, 1.25 * bar) * fps // 1) / fps


def quantise_up(seconds: float, fps: int = 24) -> float:
    """A duration rounded UP to whole frames so a floor stays a floor."""
    return -(-seconds * fps // 1) / fps


def usable_events(events: list[float], duration: float, fps: int = 24) -> list[float]:
    """L0 events the walk can cut on: inside the span, a shot apart, on frames."""
    kept: list[float] = []
    for event in sorted(quantise(e, fps) for e in events):
        if event < MIN_SHOT - EPS or event > duration + EPS:
            continue
        if kept and event - kept[-1] < MIN_SHOT - EPS:
            continue
        kept.append(event)
    return kept


def grid_points(metre, fps: int = 24) -> list[tuple[float, int]]:
    """(time, level) for L1 downbeats, L2 beats and L3 half-beats, on frames."""
    downbeats = set(metre.downbeats)
    points = [(quantise(b, fps), 1 if b in downbeats else 2) for b in metre.beats]
    halves = [(quantise((a + b) / 2, fps), 3) for a, b in zip(metre.beats, metre.beats[1:])]
    return sorted(set(points + halves))


def walk_length(position: float, beat: float, stretch: float, cap: float) -> float:
    """The arc's target at this position, expressed in whole beats under the cap."""
    target = target_length(position) * stretch
    counts = next(c for limit, c in BEATS_BY_POSITION if position < limit)
    allowed = [n for n in counts if MIN_SHOT - EPS <= n * beat <= cap + EPS]
    if not allowed:
        allowed = [n for n in (0.5, 1, 2, 3, 4, 6, 8) if MIN_SHOT - EPS <= n * beat <= cap + EPS]
    return min(allowed, key=lambda n: abs(n * beat - target)) * beat if allowed else cap


def nearest_grid(nominal: float, ahead: list[tuple[float, int]], beat: float) -> float | None:
    """The highest-level grid point near the nominal cut, else the nearest."""
    close = [g for g in ahead if abs(g[0] - nominal) <= 0.6 * beat]
    if close:
        return min(close, key=lambda g: (g[1], abs(g[0] - nominal)))[0]
    return min(ahead, key=lambda g: abs(g[0] - nominal))[0] if ahead else None


def respect_event(landed: float, event: float | None, ahead: list[tuple[float, int]],
                  ceiling: float, fps: int = 24) -> float:
    """No shot straddles an L0 event or leaves a flash frame in front of one."""
    if event is None:
        return landed
    if event <= ceiling + EPS:
        return event if landed >= event - MIN_SHOT - EPS else landed
    if event - landed < MIN_SHOT - EPS:
        before = [g for g, _ in ahead if g <= event - MIN_SHOT + EPS]
        return max(before) if before else quantise(event - MIN_SHOT, fps)
    return landed


def land(nominal: float, last: float, grid: list[tuple[float, int]], events: list[float],
         cap: float, beat: float, fps: int = 24) -> float:
    """Where the next cut goes: on the grid near the nominal, bounded by events."""
    floor, ceiling = last + MIN_SHOT, last + cap
    ahead = [g for g in grid if floor - EPS <= g[0] <= ceiling + EPS]
    event = next((e for e in events if e >= floor - EPS), None)
    landed = nearest_grid(nominal, ahead, beat)
    if landed is None:
        landed = quantise_up(min(max(nominal, floor), ceiling), fps)
    return respect_event(landed, event, ahead, ceiling, fps)


def hold_span(metre, duration: float, cap: float, fps: int = 24) -> tuple[float, float] | None:
    """(start, end) of the one shot allowed past the cap.

    With a title moment the hold ENDS on the hit and begins on the latest
    beat that puts the whole pre-title trough inside it; without one it
    opens at the corpus breath.  A downbeat start is preferred when it does
    not push the hold past two bars and a beat.
    """
    beat = metre.beat
    stop = [s for s in metre.stopdowns if metre.title_hit and metre.title_hit - 6 <= s < metre.title_hit]
    if metre.title_hit and stop and metre.title_hit <= duration + EPS:
        end = quantise(metre.title_hit, fps)
        starts = [quantise(b, fps) for b in metre.beats if b <= stop[-1] + EPS and end - b > cap + EPS]
        start = next((s for s in reversed(starts) if s in {quantise(d, fps) for d in metre.downbeats}
                      and end - s <= 2 * metre.bar + beat + EPS), starts[-1] if starts else None)
        return (start, end) if start is not None and start >= MIN_SHOT else None
    return hold_at_breath(metre, duration, cap, fps)


def hold_at_breath(metre, duration: float, cap: float, fps: int = 24) -> tuple[float, float] | None:
    """A hold opening on the first downbeat past the corpus breath."""
    start = next((quantise(d, fps) for d in metre.downbeats or metre.beats
                  if d >= HOLD_POSITION * duration), None)
    if start is None:
        return None
    end = next((quantise(b, fps) for b in metre.beats if b - start > cap + EPS), None)
    if end is None or end > duration - MIN_SHOT + EPS:
        return None
    return start, end


def close(points: list[float], duration: float, fps: int = 24) -> list[float]:
    """End the cut exactly on `duration` without a flash frame before it."""
    end = quantise(duration, fps)
    if len(points) > 1 and 0 < end - points[-1] < MIN_SHOT - EPS:
        points.pop()
    if end - points[-1] > EPS:
        points.append(end)
    return points


def plan_cuts(metre, events: list[float], duration: float,
              stretch: float = LITERARY_STRETCH, fps: int = 24) -> list[float]:
    """The beat walk: shot boundaries in whole beats, on every L0 event, one hold.

    Constants filter BEFORE the arc: a beat count is allowed only if it lies
    between MIN_SHOT and the cap, and the arc chooses among what is allowed,
    so no tempo can make the walk emit a flash frame or an overlong shot.
    """
    cap, beat = max_shot(metre.bar, fps), metre.beat
    hold = hold_span(metre, duration, cap, fps)
    l0 = usable_events(events + list(hold or ()), duration, fps)
    l0 = [e for e in l0 if not hold or not hold[0] < e < hold[1]]
    grid = grid_points(metre, fps)
    points = [0.0]
    while points[-1] < duration - MIN_SHOT + EPS:
        if hold and abs(points[-1] - hold[0]) < EPS:
            points.append(hold[1])
            continue
        position = points[-1] / max(duration, EPS)
        nominal = points[-1] + walk_length(position, beat, stretch, cap)
        points.append(land(nominal, points[-1], grid, l0, cap, beat, fps))
    return close(points, duration, fps)
