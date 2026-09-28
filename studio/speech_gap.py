"""The longest hole in speech, measured from the placed lines: QC's wall, at step 05.

ep13 (finding 64): the plan battery read the PROJECTED gap and passed; the
measured timeline carried 6.72 s against the 6.0 s wall and QC found it only
after five masters.  The measure lives here so the timeline step and QC ask
the same question of the same numbers.
"""
from __future__ import annotations

MAX_GAP_S = 6.0
"""The longest hole in speech a delivered master may carry (ep10 synthesis
B6/F6; Scarlet ep05 4.4 s, ep07 4.5 s, ep09 3.25 s pass; ep10's 11.25 s fails)."""


def gaps(lines: list[dict], until: float) -> list[tuple[float, float]]:
    """(start, end) of every hole between the placed lines, the tail included."""
    ordered = sorted(lines, key=lambda line: line["at"])
    out, end = [], ordered[0]["at"] if ordered else 0.0
    for line in ordered:
        out.append((end, line["at"]))
        end = max(end, line["at"] + line["seconds"])
    return out + [(end, until)]


def longest_gap(lines: list[dict], until: float) -> float:
    holes = gaps(lines, until)
    return round(max(b - a for a, b in holes), 2) if holes else until


def refusal(placed: dict) -> str | None:
    """Why this timeline may not render, or None: the gap, and the shot it opens in."""
    if not placed.get("lines"):
        return None
    holes = gaps(placed["lines"], placed.get("duration_s", 0.0))
    if not holes:
        return None
    start, end = max(holes, key=lambda h: h[1] - h[0])
    if end - start <= MAX_GAP_S:
        return None
    shot = next((s["index"] for s in placed.get("shots", []) if s["t_start"] <= start < s["t_end"]), "?")
    return (f"REFUSED: a {end - start:.2f} s hole in speech from {start:.2f} s (shot {shot}) against the "
            f"{MAX_GAP_S} s wall; shorten the holds (beat_s/coda_s) of the shots in it, or give one a line")
