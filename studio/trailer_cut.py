"""How long each shot is allowed to be.

Measured across 50 released trailers (Redfern's US Horror Trailers data set,
CC-BY): median shot length opens near 1.5s, dips to 1.33s for a breath around
a third of the way in, accelerates to a 0.54s trough at 85-90%, then
DECELERATES into a final hold of ~3.0s.  Loudness peaks in the same 80-90%
band and collapses in the last tenth -- the stopdown.

The arc is a diagnostic prior, not a target: Derek Lieu is explicit that no
average shot length makes a trailer better or worse.  What IS a defect is
uniformity -- every shot the same length is the single most-named amateur
tell, and it is the default failure of a generated pipeline, because clips
come out of the model at a fixed size.  So this module's job is not to hit the
curve.  It is to guarantee variety and shape.
"""
from __future__ import annotations

ARC: list[tuple[float, float]] = [
    (0.00, 1.50), (0.05, 1.17), (0.10, 1.10), (0.15, 1.06), (0.20, 1.06),
    (0.25, 1.17), (0.30, 1.33), (0.35, 1.08), (0.40, 1.07), (0.45, 1.04),
    (0.50, 1.00), (0.55, 0.88), (0.60, 0.83), (0.65, 0.78), (0.70, 0.76),
    (0.75, 0.70), (0.80, 0.74), (0.85, 0.54), (0.90, 1.12), (0.95, 2.32),
]
"""(fractional position, median shot length in seconds) -- the measured shape."""

FINAL_HOLD = 3.0
"""Median last shot across the corpus.  The title needs somewhere to sit."""


def target_length(position: float) -> float:
    """The corpus median shot length at a fractional position in the trailer."""
    if position >= ARC[-1][0]:
        return ARC[-1][1]
    for (low, length), (high, _) in zip(ARC, ARC[1:]):
        if low <= position < high:
            return length
    return ARC[0][1]


def is_uniform(lengths: list[float], tolerance: float = 0.05) -> bool:
    """True when every shot is effectively the same length -- the amateur tell.

    This is the check that matters most for a generated trailer, because a
    model hands back clips of one fixed size and concatenating them IS the
    defect.  Two shots cannot establish a pattern, so anything shorter than
    three is not uniform, it is just short.
    """
    if len(lengths) < 3:
        return False
    return max(lengths) - min(lengths) <= tolerance
