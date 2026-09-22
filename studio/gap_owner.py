"""Which shot is a silent gap made of?

QC walls the longest stretch of the cut with no voice in it. The number alone
does not say what to do about it, and the obvious reading -- the shots around
it hold too long -- is usually wrong. A gap that contains a SILENT shot is
made of that shot: it contributes its whole length to the hole by definition,
and no amount of trimming its neighbours changes that.

The cures, in order, are in docs/calibration/silent_gaps.md: give the silent
shot a line, or move the silence to a short shot with lines on both sides.
Trimming a coda comes last, because a coda is the room a move finishes in
(docs/calibration/frozen_starts.md, measured on ep08 T16).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Owner:
    """The shots a gap lies across, and the silent ones among them."""
    shots: list[int]
    silent: list[int]
    said: str


def shots_in(shots: list[dict], begins: float, ends: float) -> list[int]:
    """Every shot whose own span overlaps the gap, in order."""
    return [s["index"] for s in sorted(shots, key=_began)
            if _began(s) < ends and _ended(s) > begins]


def _began(shot: dict) -> float:
    """A placed shot says `t_start`; a fixture may say `at`."""
    return float(shot["t_start"] if "t_start" in shot else shot["at"])


def _ended(shot: dict) -> float:
    if "t_end" in shot:
        return float(shot["t_end"])
    return _began(shot) + float(shot["seconds"])


def owner(shots: list[dict], begins: float, ends: float, silent: list[int]) -> Owner:
    """The gap, read as the shots it is made of."""
    across = shots_in(shots, begins, ends)
    quiet = [i for i in across if i in silent]
    return Owner(across, quiet, _said(across, quiet, ends - begins))


def _said(across: list[int], quiet: list[int], length: float) -> str:
    """The sentence QC prints: the shot to change, or that there is none."""
    where = ", ".join(str(i) for i in across) or "nothing"
    if quiet:
        which = ", ".join(f"shot {i}" for i in quiet)
        return (f"{length:.2f}s of silence across shots {where}; {which} is silent and "
                f"is what the gap is made of -- give it a line, or move the silence "
                f"(docs/calibration/silent_gaps.md)")
    return (f"{length:.2f}s of silence across shots {where}, and no silent shot in it: "
            f"the holds are what is long, so shorten a line's beat before its coda")


def longest_span(lines: list[dict], until: float) -> tuple[float, float]:
    """(begins, ends) of the longest hole in speech -- the same hole `qc.py`'s
    `longest_gap` measures, but placed, so the shot that owns it can be named.

    The run-out is measured to the PICTURE's end, not the last line's start:
    with the start, the final hole is negative and `max` throws the tail away
    (ep03 reported 2.03 s over a 3.26 s run-out).
    """
    ordered = sorted(lines, key=lambda line: line["at"])
    if not ordered:
        return (0.0, until)
    spans, end = [], ordered[0]["at"]
    for line in ordered:
        spans.append((end, max(end, line["at"])))
        end = max(end, line["at"] + line["seconds"])
    spans.append((end, max(end, until)))
    spans.insert(0, (0.0, ordered[0]["at"]))
    return max(spans, key=lambda s: s[1] - s[0])
