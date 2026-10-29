"""G-PEOPLE: a duplicated or extra person is a wrong picture, never a flag (owner 2026-10-28).

The content gates already read it -- an extra figure ("3 figure(s) for 1 declared"), a twin
(G-TWIN) and two faces read as one man (clones) -- and every terminal used to ship it flagged.
This names those faults once, for the take (G-DEAD) and the master (the ladder's terminal)."""
from __future__ import annotations

import re

EXTRA = re.compile(r"\b\d+ figure\(s\) for \d+ declared\b")
"""panel_content's over-count line: more figures than the shot casts, or copies among them."""
KINDS = frozenset({"twin", "clones"})


def wrong_line(text: str) -> bool:
    """One content fault line naming a duplicated or extra person (G-WHO's `who:` among them)."""
    return str(text).startswith(("twin", "who:", "who (head):")) or bool(EXTRA.search(str(text)))


def wrong(fault) -> bool:
    """A take-eye or master-eye fault (dict or Fault) about a wrong person."""
    f = fault.model_dump() if hasattr(fault, "model_dump") else dict(fault)
    lines = (f.get("evidence") or {}).get("faults") or []
    return f.get("kind") in KINDS or wrong_line(f.get("note") or "") or any(wrong_line(g) for g in lines)


def takes(faults: list) -> set[int]:
    """The take indexes (`T06` -> 6) a list of take-eye faults names a wrong person on."""
    from studio import dead_footage
    out = set()
    for f in faults:
        d = f.model_dump() if hasattr(f, "model_dump") else f
        if wrong(d) and (index := dead_footage.take_of(d.get("where"))) is not None:
            out.add(index)
    return out
