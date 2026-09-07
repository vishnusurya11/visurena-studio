"""What the cue supplies the editor: cut points, and the waits between them.

THE BRICK.  A cut point must be an attack -- `trailer_edit` picks its cuts from
`beatmap.onsets` -- and no shot may run past `MAX_SHOT` (4.0 s).  So a cue that
leaves a longer wait than that inside the music it is playing forces the editor
to break one of the two rules: hold a shot past the ceiling, or cut on silence.
Neither is the editor's fault and neither can be fixed downstream.

MEASURED, run 19 (the third trailer the owner called "not dramatic enough"):
cue-1002 gave 26 attacks over 113.8 s of material -- one every 4.4 s -- for a
cut that needed 27 cuts, and its longest wait ran 17.5 s.  plan.json shows what
that bought: 23 spans, mean 5.07 s, one held 17.51 s.  The other seeds were no
better (1001: 0.80 attacks/bar, 1004: 0.31).  Nothing in step 03 read any of it.

`cue_arc.ride` is a per-bar gain and `cue_voicing.voice` is an FFT convolution:
both preserve attack COUNT exactly.  So no amount of level or spectrum work can
move this number -- BUILD rows 62, 63 and 64 were incapable of it by
construction.  Only the caption can ask for attacks, and only this module can
say whether they arrived.
"""
from __future__ import annotations

import math

import numpy as np
from pydantic import BaseModel

from studio import beatmap
from studio.trailer_edit import MAX_SHOT

CANDIDATES_PER_SHOT = 1.5
"""How many cut points a shot must be able to choose BETWEEN.  Not invented
here: `beatmap.GRID_DB` was set to 4.0 dB because at that threshold a cue
yields "roughly 1.5 candidates per shot: enough to choose from, not so many
that 'on the grid' stops meaning anything"."""


def attacks(times: np.ndarray, db: np.ndarray) -> list[float]:
    """The cut points the cue offers, read with the detector the editor cuts on."""
    return beatmap.onsets(times, db)


def material(until: float, dropouts: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """The stretches of cue that are playing: everything up to `until` less the
    dropouts the arc asked for.  A hole is not the editor waiting."""
    spans, start = [], 0.0
    for hole_start, hole_end in sorted(dropouts):
        if hole_start > start:
            spans.append((start, min(hole_start, until)))
        start = max(start, hole_end)
    if start < until:
        spans.append((start, until))
    return [(a, b) for a, b in spans if b > a]


def waits(found: list[float], spans: list[tuple[float, float]]) -> list[float]:
    """Every gap the editor must cover with one shot: inside each stretch of
    material, from its start to its first attack, between attacks, and from
    the last attack to its end."""
    out = []
    for start, end in spans:
        marks = [start] + [t for t in found if start < t < end] + [end]
        out.extend(b - a for a, b in zip(marks, marks[1:]))
    return out


def longest_wait(found: list[float], spans: list[tuple[float, float]]) -> float:
    """The longest stretch of playing music with no cut point in it."""
    return max(waits(found, spans), default=0.0)


def to_last_attack(spans: list[tuple[float, float]],
                   found: list[float]) -> list[tuple[float, float]]:
    """The stretches with the final one ending at its last cut point.  The cut
    ends on the hard out and the card holds to the stop, so music after the
    last attack is where the picture ARRIVES -- not a shot that ran out."""
    if not spans or not found:
        return spans
    start, end = spans[-1]
    inside = [t for t in found if start <= t < end]
    return spans[:-1] + ([(start, max(inside))] if inside else [])


class Supply(BaseModel):
    """What one graded cue offers the editor."""

    count: int
    per_bar: float
    per_shot: float
    longest_wait: float
    seconds: float

    @property
    def starves(self) -> bool:
        """Whether the editor is forced to break a rule to cut this cue."""
        return self.longest_wait > MAX_SHOT or self.per_shot < CANDIDATES_PER_SHOT

    @property
    def why(self) -> str:
        return (f"{self.count} attacks, {self.per_shot:.2f}/shot against "
                f"{CANDIDATES_PER_SHOT}, longest wait {self.longest_wait:.1f}s "
                f"against MAX_SHOT {MAX_SHOT}")


def supply(times: np.ndarray, db: np.ndarray, bar: float, until: float,
           dropouts: list[tuple[float, float]],
           holds: list[tuple[float, float]] | None = None) -> Supply:
    """What the cue supplies over the material it plays before its stop.

    `holds` are the stretches the ask rode LOW.  The ceiling on a wait does not
    bind there: `cue_qc.long_shots_on_holds` already says a long shot belongs
    over a sustain or a trough, so a cue that goes quiet on purpose is resting
    the picture, not starving it."""
    spans = material(until, dropouts)
    found = [t for t in attacks(times, db) if any(a <= t < b for a, b in spans)]
    playing = sum(b - a for a, b in spans)
    at_level = to_last_attack(material(until, sorted(dropouts + list(holds or []))), found)
    shots = max(1.0, math.ceil(playing / MAX_SHOT))
    return Supply(count=len(found), per_bar=len(found) / max(1.0, playing / bar),
                  per_shot=len(found) / shots, longest_wait=longest_wait(found, at_level),
                  seconds=playing)
