"""The lint on AUTOMATIC camera text: what a cure or a ladder rung writes into a
camera head, and what the take prompt keeps of it.

Jekyll ep01 (2026-10-13, docs/audit/2026-10-13_jekyll_ep01_review/MOTION.md cause 6):
the rebalance cure and the ladder wrote "toward the face of the man about" (a
name cut at six words), "pans from the third to the coat" (a layout word as an
aim), "beside the lawyer's shoulder across the whole" (the old head's tail kept
as the aim), and the prompt said "at a good walk at a normal walking pace".  And
"a few yards", "a few paces", "a man's height" survived the amount strip -- H3
obeys direction, not amount (memory: H3 obeys direction, not amount).

A garbled aim is REFUSED where a cure chooses among candidates
(move_rebalance.head_faults) and REPAIRED where one aim must be written
(take_ladder.aim_of); distances and a second pace are stripped from the prompt.
$0, pure, book-neutral.
"""
from __future__ import annotations

import re

from studio.episode_ref_official import AMOUNT

DISTANCE = (r"\b(?:a few|several|a couple of|a|an|one|two|three|four|five|ten|twenty)\s+"
            r"(?:yards?|feet|foot|inches|metres?|meters?|paces|steps)\b"
            r"|\ba (?:man's|person's|figure's|body's) (?:height|length)\b")
AMOUNTS = re.compile(AMOUNT.pattern + "|" + DISTANCE, re.I)
"""Every travel amount: the plans' own ladder words and the distances they also write."""
SAID = re.compile(r",?\s*(?:travelling\s+|for\s+)?(?:" + AMOUNTS.pattern + r")", re.I)

AIM = re.compile(r"\b(?:toward|towards|from|to|past|beside|behind|above|on|at)\s+"
                 r"(the\s+[A-Za-z'’ -]+?)(?=\s*(?:[,;.]|$|\btravelling\b|\bto\b))", re.I)
TAIL = {"about", "as", "of", "to", "the", "a", "an", "with", "and", "at", "in", "on", "from", "for",
        "across", "by", "into", "over", "toward", "towards", "his", "her", "its", "their"}
"""A word an aim never ends on: the phrase was cut mid-name or mid-clause."""
LAYOUT = {"third", "thirds", "quarter", "half", "edge", "edges", "foreground", "background", "middle",
          "frame", "height"}
"""A share of the picture, never a thing a camera aims at ("from the LEFT third").  A side
("from the left to the right") is a direction and stays; a corner can be a street's."""
OLD_TAIL = re.compile(r"\s+(?:across the whole|travelling)\b.*$", re.I)
PACE = re.compile(r"\s*\bat a (?:good |brisk |steady |smart |normal |quick |fast |easy )?"
                  r"(?:walk|walking pace|pace|trot|clip|run)\b", re.I)


def aims(text: str) -> list[str]:
    """The aim phrases of a camera head: "the face of the lawyer", "the coat"."""
    head = (text or "").split(";")[0]
    return [m.group(1).strip() for m in AIM.finditer(head)]


def aim_faults(aim: str) -> list[str]:
    words = aim.lower().replace("’", "'").split()
    out = []
    if re.search(r"\bacross the whole\b(?! shot)", aim, re.I):
        out.append(f"the aim {aim!r} carries the old head's tail")
    elif words and words[-1] in TAIL:
        out.append(f"the aim {aim!r} is cut mid-phrase (ends on {words[-1]!r})")
    if words and words[-1] in LAYOUT:
        out.append(f"the aim {aim!r} is a layout word, not a thing")
    return out


def faults(text: str) -> list[str]:
    """Why this automatic camera text must not be written: a garbled aim or a pace said twice."""
    out = [f for a in aims(text) for f in aim_faults(a)]
    if len(PACE.findall(text or "")) > 1:
        out.append("a pace is said twice")
    return out


def repair_aim(aim: str) -> str:
    """The aim without the old head's tail and without the words it was cut on."""
    words = OLD_TAIL.sub("", aim or "").split()
    while words and words[-1].lower() in TAIL:
        words.pop()
    return " ".join(words)


def strip_amounts(text: str) -> str:
    """The camera text with every travel amount and distance gone."""
    out = " ".join(SAID.sub("", text or "").split())
    return re.sub(r"\s+,", ",", out).strip(" ,")


def has_pace(text: str) -> bool:
    return bool(PACE.search(text or ""))


def one_pace(text: str) -> str:
    """The text with every pace after the first removed."""
    found = list(PACE.finditer(text or ""))
    for m in reversed(found[1:]):
        text = text[:m.start()] + text[m.end():]
    return text
