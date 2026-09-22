"""What is in the TAKE, read across its frames and judged here.

`panel_content` reads the storyboard panel. The panel is not what ships. ep07's
T26 rendered a grey-haired woman in an apron where both the panel and the cast
sheet show a woman of twenty-nine, and the only reason anyone knows is that
somebody opened the file.

A take is judged on the same closed vocabulary as a panel, from frames sampled
past H3's one-second reference leak, with two differences the video makes
necessary: a figure may walk in, so the count is the MOST seen in any frame;
and a copy matters most, because identity drift is the fault that has needed
an eye every time.
"""
from __future__ import annotations

import re

from studio.panel_content import Seen, faults

HAIR = ("grey hair", "gray hair", "white hair", "bald", "red hair", "blonde hair",
        "black hair", "brown hair", "auburn hair", "chestnut hair", "dark hair")
"""Hair a reader may name. A row that says one colour and a take that shows
another are two different people, and the cut carries the wrong face."""

WORD = re.compile(r"[a-z]+")


def busiest(reads: list[Seen]) -> Seen:
    """The take at its fullest: the most figures any frame held, the most
    copies, any lettering, and every subject seen in any of them.

    A figure who walks in halfway is still in the take. An average would put
    him at two thirds of a person and let him ship.
    """
    if not reads:
        raise ValueError("a take with no frames read is not a clean take")
    subjects: list[str] = []
    for read in reads:
        for subject in read.subjects:
            if subject not in subjects:
                subjects.append(subject)
    fullest = max(reads, key=lambda r: r.people)
    return Seen(
        landform=fullest.landform,
        people=max(r.people for r in reads),
        lookalikes=max(r.lookalikes for r in reads),
        text=any(r.text for r in reads),
        hour=fullest.hour,
        subjects=subjects,
    )


def drifted(seen: Seen, physical: str) -> list[str]:
    """Hair the cast row rules out, seen in the take.

    MEASURED on ep07 T26: the take showed grey hair on a woman whose row says
    thick chestnut-auburn. Nothing compared them.
    """
    if not physical:
        return []
    said = " ".join(seen.subjects).lower()
    row = physical.lower()
    return [h for h in HAIR if h in said and h.split()[0] not in row]


def take_faults(reads: list[Seen], planned: int, crowd: bool, flat: bool,
                night: bool, physical: str, frame: str, banned=()) -> list[str]:
    """Every way this take disagrees with the shot that asked for it."""
    seen = busiest(reads)
    out = faults(seen, frame=frame, planned=planned, crowd=crowd, flat=flat,
                 night=night, banned=banned, physical=physical)
    out += [f"{h} where the row says otherwise" for h in drifted(seen, physical)]
    return out
