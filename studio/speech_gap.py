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

HOLE_MARGIN_S = 0.5
"""How far under MAX_GAP_S the plan battery projects a hole before refusing it.

MEASURED on ep17/ep18: a hole's projected length at the series rate matches
the measured hole to within 0.04 s (ep17 4.70 projected vs 4.73 measured;
ep18 5.50 vs 5.54; pre-fix ep18's plan.json.bak_hole projected its hole at
12.5 and timeline.py refused 12.52).  The mechanism: a hole contains no
spoken words, so its length is only HANDLE 0.25 x2 + BREATH 0.70 + beat_s +
coda_s constants plus the on_frame ceiling (<= 1/24 s per shot boundary) --
the narrator's rate error never enters a hole.  0.5 s is 10x the observed
error and aligns with the holds cure's existing HOLE_WALL_S - 0.5 target."""


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


def over_wall(placed: dict, wall: float) -> list[tuple[float, float, list[int]]]:
    """Every (start, end, shot_indices) hole longer than `wall`, in time order.

    `refusal()` generalized to ALL holes over a given wall: the plan battery
    projects against MAX_GAP_S - HOLE_MARGIN_S, the cures trim to the same
    number, and step 05 keeps refusing at MAX_GAP_S via `refusal`."""
    if not placed.get("lines"):
        return []
    out = []
    for start, end in gaps(placed["lines"], placed.get("duration_s", 0.0)):
        if end - start <= wall:
            continue
        shots = [s["index"] for s in placed.get("shots", [])
                 if s["t_start"] < end and s["t_end"] > start]
        out.append((start, end, shots))
    return out


def refusal(placed: dict) -> str | None:
    """Why this timeline may not render, or None: the gap, and the shot it opens
    in -- the largest-hole special case of `over_wall` at MAX_GAP_S."""
    holes = over_wall(placed, MAX_GAP_S)
    if not holes:
        return None
    start, end, _ = max(holes, key=lambda h: h[1] - h[0])
    shot = next((s["index"] for s in placed.get("shots", []) if s["t_start"] <= start < s["t_end"]), "?")
    return (f"REFUSED: a {end - start:.2f} s hole in speech from {start:.2f} s (shot {shot}) against the "
            f"{MAX_GAP_S} s wall; shorten the holds (beat_s/coda_s) of the shots in it, or give one a line")


SPEECH_OVER_GAP_DB = 11.0
"""Speech over the gaps between lines, RMS dB.  OWNER 2026-09-27 on ep13
master_iter8 (10.9): "the sound effects are good but too loud".  WotW ep10-12
measured 11.3-13.5, Sherlock 9.8-16.5; iter11 after the duck and trim 12.0."""


def _db(x) -> float:
    import numpy as np
    return float(20 * np.log10(np.sqrt(np.mean(np.square(x))) + 1e-9)) if len(x) else -120.0


def speech_over_gaps(audio, sr: int, lines: list[dict], until: float) -> float:
    """Mean dB under the lines minus mean dB of the gaps (a second or longer) between them."""
    import numpy as np
    said = [_db(audio[int(l["at"] * sr):int((l["at"] + l["seconds"]) * sr)]) for l in lines]
    holes = [(a + 0.2, b - 0.2) for a, b in gaps(lines, until) if b - a > 1.0]
    quiet = [_db(audio[int(a * sr):int(b * sr)]) for a, b in holes]
    return round(float(np.mean(said) - np.mean(quiet)), 2) if said and quiet else 99.0


def band_ok(db: float) -> bool:
    return db >= SPEECH_OVER_GAP_DB
