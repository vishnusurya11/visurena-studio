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


CONFIRM_FRAMES = 2
"""Frames of one shot that must agree before a per-frame people read blocks the master (brick 17)."""
LOOK_FRAMES = 3
"""Frames a shot must have been read on before a lone people read may stand down; fewer fails closed."""


def _dict(fault) -> dict:
    return fault.model_dump() if hasattr(fault, "model_dump") else dict(fault)


def per_frame_people(fault) -> bool:
    """A master read's people line on one frame, with nothing on it that stands on one sighting."""
    f = _dict(fault)
    if f.get("kind") != "content" or (f.get("evidence") or {}).get("at") is None:
        return False
    hard = any(line.startswith(SCAFFOLD_LINE) or line.endswith(HAIR_LINE) for line in lines_of(f))
    return blocks(f) and not hard and not long_leak(f)


def _confirmed(rows: list[dict]) -> bool:
    """Two frames agree, or the shot was read too thinly for a lone frame to stand down."""
    ats = {r["evidence"]["at"] for r in rows}
    read_on = max(int(r["evidence"].get("read_on") or 0) for r in rows)
    return len(ats) >= CONFIRM_FRAMES or read_on < LOOK_FRAMES


def master_blocks(faults: list) -> dict[str, list[dict]]:
    """Shot -> the faults that refuse it at the master (Jekyll ep07 retro S1)."""
    out: dict[str, list[dict]] = {}
    lone: dict[str, list[dict]] = {}
    for f in map(_dict, faults):
        if per_frame_people(f):
            lone.setdefault(f.get("where"), []).append(f)
        elif blocks(f):
            out.setdefault(f.get("where"), []).append(f)
    for where, rows in lone.items():
        if _confirmed(rows):
            out.setdefault(where, []).extend(rows)
    return out


def lone_people_shots(faults: list) -> list[int]:
    """The shot indexes whose only people read is one frame: the second look reads more of them."""
    seen: dict[str, set] = {}
    for f in filter(per_frame_people, map(_dict, faults)):
        seen.setdefault(f["where"], set()).add(f["evidence"]["at"])
    return sorted(int(w.split("_")[1]) for w, ats in seen.items() if len(ats) == 1 and w.startswith("shot_"))


def block_text(where: str, rows: list[dict]) -> str:
    """`shot_07: <line> at 0.5s (2 of 4 frames)`: what a reader needs to act on the refusal."""
    lines = [ln for r in rows for ln in lines_of(r) if ln]
    line = lines[0] if lines else rows[0].get("kind", "?")
    framed = [r for r in rows if (r.get("evidence") or {}).get("at") is not None]
    if not framed:
        return f"{where}: {line}"
    ats = sorted({r["evidence"]["at"] for r in framed})
    read_on = max(int(r["evidence"].get("read_on") or 0) for r in framed)
    return f"{where}: {line} at {ats[0]}s ({len(ats)} of {read_on} frames)"


def takes(faults: list) -> set[int]:
    """The take indexes (`T06` -> 6) a list of take-eye faults blocks."""
    from studio import dead_footage
    out = set()
    for f in faults:
        d = f.model_dump() if hasattr(f, "model_dump") else f
        if blocks(d) and (index := dead_footage.take_of(d.get("where"))) is not None:
            out.add(index)
    return out
