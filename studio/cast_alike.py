"""G-ALIKE: two cast who read as one person never share a shot (owner 2026-10-28, a hard check).

A face read sees the figure, the hair and the facial hair; clothes are what the video model swaps
(Jekyll ep05: H3 drew Jekyll in Utterson's bowler, two Uttersons in one frame).  Two look rows that
agree on those three are one person to the model, whatever they wear.  The cure is a redrawn base
sheet, never the plan's words, so the row is tier 1 and step 06 repeats it."""
from __future__ import annotations

import itertools
import json
from pathlib import Path

NEAR = {frozenset({"grey", "white"})}
"""Hair colours one notch apart: the same head at two distances (describe.NEIGHBOURS)."""


def alike(a: tuple[str, str, str], b: tuple[str, str, str]) -> bool:
    """(figure, hair colour, facial hair) agreeing on all three; an unread marker never agrees."""
    if not all(a) or not all(b):
        return False
    return a[0] == b[0] and a[2] == b[2] and (a[1] == b[1] or frozenset((a[1], b[1])) in NEAR)


def marks(book) -> dict[str, tuple[str, str, str]]:
    """{cast id: (figure, hair colour, facial hair)} from refs/looks.json's base look and refs.json's
    gender; {} for a book with no look rows."""
    looks_path, refs_path = Path(book) / "refs" / "looks.json", Path(book) / "refs" / "refs.json"
    if not looks_path.exists() or not refs_path.exists():
        return {}
    gender = {r.get("entity_id"): r.get("gender") or "" for r in json.loads(refs_path.read_text(encoding="utf-8"))["refs"]}
    out = {}
    for cid, row in json.loads(looks_path.read_text(encoding="utf-8"))["characters"].items():
        said = ((row.get("looks") or {}).get(row.get("base")) or {}).get("markers") or {}
        out[cid] = (gender.get(cid, ""), said.get("hair_colour", ""), said.get("facial_hair", ""))
    return out


def faults(shots: list[dict], marks_: dict[str, tuple[str, str, str]]) -> list[str]:
    """One line per shot staging two alike cast."""
    out = []
    for shot in shots:
        for a, b in itertools.combinations(sorted(set(shot.get("faces") or [])), 2):
            if a in marks_ and b in marks_ and alike(marks_[a], marks_[b]):
                figure, hair, face = marks_[a]
                out.append(f"G-ALIKE shot {shot.get('index')}: {a!r} and {b!r} read as one person ({figure}, "
                           f"{hair} hair, facial hair {face}); only their clothes differ, which the video model "
                           f"swaps -- redraw one base sheet (hair or facial hair) before this episode renders")
    return out
