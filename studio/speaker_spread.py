"""One speaker, one voice: a part's lines measured against EACH OTHER.

MEASURED on WotW ep05 (2026-09-20).  `say_lines` scores every render against
the character's DESIGN clip and never against that character's other lines, so
a part can pass twice and still be two men: the neighbour's two lines, l05 at
sunset and l24 by firelight, each passed their floor and measured 0.58 against
each other.  The audience never hears the design clip; it hears l05 and l24
back to back.

The cause was in the voice sheet, not the register: instructions like "an
audible wet breath between phrases", "a thick swallow" and "the final consonant
dropped entirely" are NOISE, not timbre, and on an eight-word line the noise is
most of what the ear scores.  A sheet that names register and colour only
rendered 0.922 between the same two lines.
"""
from __future__ import annotations

SAME_SPEAKER_FLOOR = 0.70
"""CALIBRATED 2026-09-20 on the episodes the owner watched and published, which
is the only calibration set that counts.  Their worst same-speaker pairs are
ep01 0.76, ep02 0.76, ep03 0.72 -- all fine to the ear.  The one genuine split
measured 0.58 (ep05's neighbour, two men in one part; rewriting the voice sheet
took the same pair to 0.922).  A floor of 0.86, which the band between DIFFERENT
characters suggested, would have condemned every episode already shipped:
a gate that accuses correct work is a threshold calibrated on the wrong world."""


def worst_pair(sims: dict[tuple[str, str], float]) -> tuple[str, str] | None:
    """The two lines of this speaker that least resemble each other."""
    return min(sims, key=sims.get) if sims else None


def spread(sims: dict[tuple[str, str], float]) -> dict:
    """Whether every pair of one speaker's lines agrees, and the worst pair."""
    worst = min(sims.values()) if sims else None
    return {"pairs": len(sims), "worst": worst, "worst_pair": worst_pair(sims),
            "ok": worst is None or worst >= SAME_SPEAKER_FLOOR}
