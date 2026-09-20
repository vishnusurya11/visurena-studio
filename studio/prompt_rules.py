"""Prompt faults measured on WotW ep01-ep03, checked before any GPU time.

Every rule here cost an episode to learn; the notes name the take.
"""
from __future__ import annotations

import re

PEOPLE = r"(?:people|men|women|workmen|figures|onlookers|soldiers|boys|girls|diggers|"\
         r"labourers|spectators|mourners|refugees)"
NUMBERED = re.compile(
    r"\b(?:(?:two|three|four|five|six|several)\s+[a-z\- ]{0,30}?" + PEOPLE + r"\b"
    r"|(?:a|the)\s+(?:dense\s+|small\s+|great\s+|thin\s+)?(?:crowd|throng|mob)\b"
    r"|(?:a|the)\s+(?:long\s+|thin\s+)?(?:stream|line|row|knot|party)\s+of\s+"
    r"[a-z\- ]{0,30}?" + PEOPLE + r"\b)", re.I)
"""ep03 T19: 'three workmen in collarless shirts and moleskin trousers' came back
as three identical men; T12/T14's 'dense crowd' and 'stream of people' as rows of
the same figure.  One description covering several people IS one figure to H3.

Both ends of the alternation need their own word boundary, and both were learned
the same way: ep04's "two immense glossy black eyes" matched `two immen` + `men`
and flagged the Martian shots, and ep05's "the linen runs out flat" matched
`the line` and flagged the white flag.  A lint that accuses correct prose is a
lint the next author switches off."""

INDIVIDUAL = re.compile(r"each turned|each in|one [a-z]+,|, a [a-z\- ]+ (?:man|woman|boy|girl)\b",
                        re.I)
PUSH = re.compile(r"\bpush(?:es|ing)? in\b", re.I)
"""ep02/ep03: every push overran 1.9-3.5x, softened, and stretched faces."""

EXIT = re.compile(r"\b(away|on along|off down|out of (?:the )?frame|into the distance|"
                  r"disappears|exits|walks off)\b", re.I)
"""ep02 T12/T21: a last clause that sends someone out of frame makes H3 follow
them and reframe in the final second."""

KEPT = re.compile(
    r"\b(?:pans?|panning|tracks?|tracking|trucks?|trucking|pulls?|pulling|pushes|pushing|"
    r"rises|rising|descends|descending|tilts?|tilting|circles|arcs?)\b"
    r"[^.]*?\bkeep(?:s|ing)\b[^.]*?\b(?:centre|center|frame|third|edge)\b", re.I)
"""ep01: 18 of 23 shots were 'pan ... X keeps the left third' -- a rotating camera
with a fixed subject is an orbit, which is what the owner saw."""


def group_once(text: str) -> bool:
    return bool(NUMBERED.search(text)) and not INDIVIDUAL.search(text)


def push_in(text: str) -> bool:
    return bool(PUSH.search(text))


def last_clause_exits(text: str) -> bool:
    return bool(EXIT.search(text.rstrip(". ").split(";")[-1]))


def kept_anchor(text: str) -> bool:
    return bool(KEPT.search(text))


def move_variety(moves: list[str]) -> dict:
    if not moves:
        return {"distinct": 0, "back_to_back": 0, "most_used_share": 0.0}
    counts = {m: moves.count(m) for m in set(moves)}
    return {"distinct": len(counts),
            "back_to_back": sum(1 for a, b in zip(moves, moves[1:]) if a == b),
            "most_used_share": round(max(counts.values()) / len(moves), 2)}


def check_shot(shot: dict) -> list[str]:
    """Every rule this shot breaks, by name."""
    frame, motion = shot.get("frame", ""), shot.get("motion", "")
    out = []
    if group_once(frame) or group_once(motion):
        out.append("group_once")
    if push_in(motion):
        out.append("push_in")
    if last_clause_exits(motion):
        out.append("exit_clause")
    if kept_anchor(motion):
        out.append("kept_anchor")
    return out
