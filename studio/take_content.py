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

from studio import panel_content as pc
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
        posture=usual_posture(reads),
    )


def usual_posture(reads: list[Seen]) -> str:
    """The posture most of the take's frames show, ties to the earliest. ep10
    T18 stood for two frames and lay for one: it reads standing, and fails."""
    said = [r.posture for r in reads if r.posture]
    return max(said, key=lambda p: (said.count(p), -said.index(p))) if said else ""


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
                night: bool, physical: str, frame: str, banned=(),
                size: str = "", extras: int = 0) -> list[str]:
    """Every way this take disagrees with the shot that asked for it -- judged
    by the same rules as its panel: the shot's size and its declared extras."""
    seen = busiest(reads)
    out = faults(seen, frame=frame, planned=planned, crowd=crowd, flat=flat,
                 night=night, banned=banned, physical=physical, size=size, extras=extras)
    out += [f"{h} where the row says otherwise" for h in drifted(seen, physical)]
    return out


# ---- the second vote: framing and action, named in a closed vocabulary --------
#
# The detector decides a count, a position, an identity or a copy; the reader
# keeps what it does well -- naming.  Its framing and action are a SECOND VOTE
# beside the plan's size and motion (decision 2026-09-24-automate-the-taste-
# gates, §1.1): a disagreement is a low fault the take eye lists, never a wall
# on its own, because the bench holds no owner row for either yet.

FRAMING = ("insert", "extreme_close", "close", "medium_close", "medium", "full", "wide")
"""The plan's own Size vocabulary, so the read and the plan compare word for word."""

ACTIONS = ("standing", "walking", "running", "sitting", "kneeling", "lying", "turning",
           "reaching", "pointing", "speaking", "writing", "climbing", "none")
"""What the MAIN figure does, one word; `none` when the reader cannot say."""

ACTION_WORDS = {
    "standing": ("stand",), "walking": ("walk", "stride", "step", "pace"),
    "running": ("run", "sprint", "dash"), "sitting": ("sit", "seat", "sat"),
    "kneeling": ("kneel", "knelt"), "lying": ("lie", "lying", "lies", "lay", "sprawl"),
    "turning": ("turn",), "reaching": ("reach",), "pointing": ("point",),
    "speaking": ("speak", "says", "talk"), "writing": ("writ", "pen"), "climbing": ("climb", "clamber"),
}
"""The motion's words that ask for each action; a stem, so "strides" answers walking."""

ASK = (pc.ASK + "\n"
       '"framing": how much of the MAIN person the frame holds, one of ' + ", ".join(FRAMING) + ".\n"
       '"action": what the MAIN person is doing, one of ' + ", ".join(ACTIONS) + ".")
"""The panel's ask plus the two take names; the same closed-list rule."""

FRAMING_SLACK = 1
"""Sizes apart a read may sit from the plan and still agree: a medium close
read as a close is the reader's eye, two sizes off is another shot."""


def framing_vote(said: str, planned: str) -> str | None:
    """The disagreement, or None when the read agrees or cannot tell."""
    if said not in FRAMING or planned not in FRAMING:
        return None
    if abs(FRAMING.index(said) - FRAMING.index(planned)) <= FRAMING_SLACK:
        return None
    return f"framing reads {said!r}, the shot is a {planned}"


def action_vote(said: str, motion: str) -> str | None:
    """An action the motion's own words never ask for, or None."""
    if said not in ACTION_WORDS:
        return None
    low = (motion or "").lower()
    if any(w in low for w in ACTION_WORDS[said]):
        return None
    return f"action reads {said!r}, the motion never asks for it"


def second_vote(said: str) -> dict:
    """The reader's framing and action from its answer, however wrapped;
    `Unreadable` without both -- never a default that agrees."""
    got = pc._loads(said)
    if isinstance(got, list) and got:
        got = pc._loads(got[0]) if isinstance(got[0], str) else got[0]
    if not isinstance(got, dict) or "framing" not in got or "action" not in got:
        raise pc.Unreadable("the reader's answer has no framing or action")
    return {"framing": str(got["framing"]).lower().strip(), "action": str(got["action"]).lower().strip()}
