"""Cells written from the picture: the setup's geometry and every shot's
`at_rest`, in the idiom that held the room in ep09-13 -- each fixed thing at a
frame THIRD and BAND in capitals ("the white gate at the CENTRE LEFT, black
smoke across the TOP third").  ep14's writer, with no picture, wrote
inventories ("the blackboard stands at the far edge; the door occupies the
near edge") in a different order per panel and the drawer rebuilt the room
per panel: 0.0 position tokens a shot against 4.2-7.7 (2026-09-28).

The writer's SUBJECT sentence is kept -- who is where, doing what -- and the
room behind it comes from the read; a wide names five things, a close one.
"""
from __future__ import annotations

import re

COUNT = {"wide": 5, "full": 4, "medium": 3, "medium_close": 2, "close": 1, "insert": 1}
"""Fixed things a shot of this size restates behind its subject."""


def phrase(t: dict) -> str:
    """One fixed thing at its third and band, by its size."""
    thing, x, y = t["thing"], t["x"], t["y"]
    if t.get("size") == "fills":
        return f"The {thing} fills the {x} third of the frame from the {y} band outward."
    if t.get("size") == "small":
        return f"The {thing} shows small at the {y} {x}, {t.get('depth', 'far')}."
    return f"The {thing} stands at the {y} {x}, {t.get('depth', 'far')}."


def geometry_of(things: list[dict]) -> str:
    """The setup's layout sentence: its five largest fixed things by frame position."""
    return " ".join(phrase(t) for t in things[:COUNT["wide"]])


def subject_of(at_rest: str) -> str:
    """The writer's first sentence: the subject, kept word for word."""
    first = re.split(r"(?<=[.;])\s", (at_rest or "").strip(), 1)[0].strip()
    return first.rstrip(";") + ("" if first.endswith(".") else ".") if first else ""


def at_rest_of(shot: dict, things: list[dict]) -> str:
    """The shot's subject sentence, then the room behind it from the picture."""
    kept = subject_of(shot.get("at_rest", ""))
    behind = " ".join(phrase(t) for t in things[:COUNT.get(shot.get("size", "medium"), 3)])
    return f"{kept} {behind}".strip()


def rewrite(doc: dict, readings: dict[str, list[dict]]) -> dict:
    """The plan with each read setup's geometry and its shots' at_rest from the picture."""
    out = {**doc, "setups": {k: dict(v) for k, v in (doc.get("setups") or {}).items()},
           "shots": [dict(s) for s in doc.get("shots") or []]}
    for setup, things in readings.items():
        if not things or setup not in out["setups"]:
            continue
        out["setups"][setup]["geometry"] = geometry_of(things)
        for shot in out["shots"]:
            if shot.get("setup") == setup:
                shot["at_rest"] = at_rest_of(shot, things)
    return out
