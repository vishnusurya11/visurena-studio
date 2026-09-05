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

FINAL_HOLD = 4.5
"""How long the card holds after the hit lands on it.

The corpus median last shot is 3.0s, and 3.0 is what run 10 held -- so the
file ended while the impact was still decaying (momentary -49 LUFS at 104.7s
of a 105.08s master) and the last thing the trailer did was cut itself off.
A synthesised impact decays over about 3s; the hold has to outlast it, and
the corpus median is a median of shots, not of buttons (D: title hold >= 4s).
"""

PRE_TITLE_SILENCE = 2.2
"""The held breath between the hard out and the hit on the card.

The norm is 1.5-2.5s.  It is not 1.5, because the rule that measures it --
momentary loudness under -35 LUFS for >= 1.5s -- reads a 400ms trailing
window, so the first 0.4s of any silence still carries the music that
preceded it and a 1.5s gap can only ever measure 1.1s.  MEASURED on the
synthetic rebuild of run 10: 2.0s of silence measures 1.5s, exactly on the
rule with nothing to spare; 2.2 measures 1.7.
"""


def title_moment(title_at: float, hold: float = FINAL_HOLD,
                 silence: float = PRE_TITLE_SILENCE) -> tuple[float, float, float]:
    """(hard out, hit, card seconds) for a picture whose last cut is `title_at`.

    The bed stops dead on the last cut, the card runs on room tone alone for
    `silence`, the hit lands, and the card holds `hold` past it so the tail
    has somewhere to decay.  Run 10 instead faded the cue over 3s into digital
    silence and struck the card at -46 LUFS, where there was no cue left.
    """
    return title_at, title_at + silence, silence + hold


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
