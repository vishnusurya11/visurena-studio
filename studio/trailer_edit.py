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
