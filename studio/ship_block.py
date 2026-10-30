"""The narrow ship-block: the settled faults that never ship flagged (owner 2026-10-30, Jekyll ep01-06 retro).

Option A (2026-10-18) ships a take the ladder kept at its cap, flagged.  G-PEOPLE (2026-10-28) took the wrong
person out of that; the retro adds the three kinds with a precise detector, each a picture no viewer forgives:
the prompt's own scaffold words read back from the picture (ep06 T19's envelope), hair no staged row allows (ep05
T07, Jekyll grey in every shot), and a plate leak of LEAK_FRAMES or more (ep04 T05/T10/T12).  Warp, gait, framing
and generic lettering stay flags: replayed on ep02-06 they park correct pictures (skeptic.md section 2)."""
from __future__ import annotations

import re

LEAK_FRAMES = 9
"""Frames of plate before the panel a take may not ship with: ep04's three confirmed leaks were 9-12."""
SCAFFOLD = ("focus", "picture", "panel", "storyboard", "framing")
"""Words the prompt builders write and no page in a story carries ("THE FOCUS OF THE PICTURE IS")."""
SCAFFOLD_LINE = "scaffold: the prompt's words drawn in the picture"
HAIR_LINE = "where the row says otherwise"


def scaffold_words(strings: list[str]) -> list[str]:
    """The scaffold words among OCR's strings, in SCAFFOLD order."""
    said = set(re.findall(r"[a-z]+", " ".join(strings).lower()))
    return [w for w in SCAFFOLD if w in said]


def scaffold_line(words: list[str]) -> str:
    return f"{SCAFFOLD_LINE} ({', '.join(words)})"


def lines_of(fault) -> list[str]:
    f = fault.model_dump() if hasattr(fault, "model_dump") else dict(fault)
    return [str(f.get("note") or "")] + [str(g) for g in (f.get("evidence") or {}).get("faults") or []]


def long_leak(fault) -> bool:
    f = fault.model_dump() if hasattr(fault, "model_dump") else dict(fault)
    frames = (f.get("evidence") or {}).get("frames")
    return f.get("kind") == "leak" and isinstance(frames, (int, float)) and frames >= LEAK_FRAMES


def blocks(fault) -> bool:
    """A settled fault that may not ship flagged: a wrong person, scaffold words, hair no row allows, a long leak."""
    from studio import people_faults
    lines = lines_of(fault)
    return (people_faults.wrong(fault) or long_leak(fault)
            or any(line.startswith(SCAFFOLD_LINE) or line.endswith(HAIR_LINE) for line in lines))


def takes(faults: list) -> set[int]:
    """The take indexes (`T06` -> 6) a list of take-eye faults blocks."""
    from studio import dead_footage
    out = set()
    for f in faults:
        d = f.model_dump() if hasattr(f, "model_dump") else f
        if blocks(d) and (index := dead_footage.take_of(d.get("where"))) is not None:
            out.add(index)
    return out
