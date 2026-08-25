"""Screenplay format primitives shared by analysis and the screenplay stage.

A slugline is `INT./EXT. LOCATION - TIME OF DAY`. Its first component comes out of
extraction, and it arrived in eight different spellings across one book — so it is
normalized here, once, rather than by whichever consumer happens to look at it.
"""

from __future__ import annotations

INT = "INT"
EXT = "EXT"
BOTH = "INT/EXT"
UNKNOWN = "UNKNOWN"

_WORDS = {
    "int": INT, "interior": INT, "inside": INT, "i": INT,
    "ext": EXT, "exterior": EXT, "outside": EXT, "e": EXT,
}   # "i"/"e" only ever appear as the industry's own I/E pair


def normalize_int_ext(raw: str | None) -> str:
    """Canonicalise the interior/exterior component of a slugline.

    Measured across A Study in Scarlet's 92 scenes, this field arrived as INT, EXT,
    UNKNOWN, INT/EXT, "INT / EXT", "EXT / UNKNOWN", EXT/INT and "EXT / INT" — eight
    spellings of three values. The cause is a skill line reading
    `int_ext: INT / EXT / UNKNOWN`, which uses " / " as a menu separator for a field
    whose own vocabulary contains a slash: INT/EXT is a real screenplay term. The
    notation collided with the values, so the model combined them.

    Order carries no meaning — a scene straddling a doorway is INT/EXT whichever half
    the writer named first. A pair with one unusable half is UNKNOWN, not a pair:
    guessing INT would be wrong about half the time, and a slugline nobody can write
    should say so."""
    parts = [p.strip().lower() for p in (raw or "").replace("|", "/").split("/")]
    found = {_WORDS[p] for p in parts if p in _WORDS}
    if len(parts) > 1 and len(found) != len(parts):
        return UNKNOWN            # a half we could not read is not a pair
    if found == {INT, EXT}:
        return BOTH
    if len(found) == 1:
        return found.pop()
    return UNKNOWN
