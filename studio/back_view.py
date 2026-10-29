"""Who a grid shows only from behind (Jekyll ep06 retro A, 2026-10-29).

An over-the-shoulder stages the near man's face sheet beside the far man's, and the drawer copies the near
face into the far slot: ep06 panels 24/25 drew Utterson twice and no Poole, one right draw in four.  A man
whose every appearance in a grid's picture words is his shoulder, his back or the back of his head shows no
face; grids.cast_of draws him from his words (hat, hair, coat) and stages no sheet for him."""
from __future__ import annotations

import re

from studio.scene_cast import PICTURE_FIELDS

BACK = (r"over the (?:near |far |left |right )?shoulder of {p}\b",
        r"{p}'s (?:[\w-]+ ){{0,2}}(?:shoulder|shoulders|back)\b",
        r"back of {p}'s",
        r"{p},? (?:seen )?from behind")
FRONT = (r"{p}'s (?:[\w-]+ ){{0,2}}(?:face|eyes|mouth)\b", r"{p} turns\b", r"{p} faces\b")


def words_of(shot) -> str:
    """The shot's picture words and its cuts', as scene_cast.in_frame reads them."""
    segs = [shot] + list(getattr(shot, "cuts", None) or [])
    return " ".join(str(getattr(seg, f, "") or "") for seg in segs for f in PICTURE_FIELDS)


def _any(patterns: tuple, phrases: list[str], text: str) -> bool:
    for said in phrases:
        p = re.escape(said.strip())
        if p and any(re.search(pat.format(p=p), text, re.I) for pat in patterns):
            return True
    return False


def named(phrases: list[str], text: str) -> bool:
    return any(s.strip() and re.search(rf"\b{re.escape(s.strip())}\b", text, re.I) for s in phrases)


def back_only(phrases: list[str], shots: list) -> bool:
    """Every shot whose picture words name this person shows his back or shoulder and never his face; False
    for a person no shot names."""
    seen = False
    for shot in shots:
        text = words_of(shot)
        if not named(phrases, text):
            continue
        seen = True
        if _any(FRONT, phrases, text) or not _any(BACK, phrases, text):
            return False
    return seen
