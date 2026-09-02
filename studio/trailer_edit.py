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

MIN_SHOT = 0.4
"""Below this a shot reads as a flash frame rather than an image."""


def snap(when: float, grid: list[float], tolerance: float = SNAP_TOLERANCE) -> float:
    """Move a cut onto a musical onset if one is within tolerance."""
    if not grid:
        return when
    nearest = min(grid, key=lambda point: abs(point - when))
    return nearest if abs(nearest - when) <= tolerance else when


def cut_points(duration: float, grid: list[float], start: float = 0.0,
               stretch: float = LITERARY_STRETCH) -> list[float]:
    """Shot boundaries across a span, following the arc and snapping to music."""
    points = [start]
    while True:
        position = (points[-1] - start) / max(duration - start, 1e-6)
        nominal = points[-1] + target_length(position) * stretch
        if nominal >= duration - 0.2:
            break
        landed = snap(nominal, grid)
        if landed <= points[-1] + 0.2:
            landed = points[-1] + target_length(position) * stretch
        points.append(round(landed, 3))
    if duration - points[-1] < MIN_SHOT and len(points) > 1:
        points.pop()          # absorb a runt tail rather than cutting to it
    points.append(duration)
    return points


def lengths_of(points: list[float]) -> list[float]:
    return [round(b - a, 3) for a, b in zip(points, points[1:])]
