"""A plan's epithet binds to the person it tags.

`cast_refs.tag(book, who, said, fragments)` writes "said (fragments)" into a plan:
"the lawyer (long, gaunt ..., black bowler hat)", "the little man (...)". The take
and grid builders bound only a person's DISPLAY name or surname, so the epithet
stayed a free noun beside "<Subject 1> is Mr. Utterson", and its parenthetical
described him a second time (Jekyll ep01 iter4: 18 takes never cited a staged
Subject; 23 described someone twice -- the ep16 duplicate class, one person told
to the model twice).

Owner ruling 2026-10-15: an epithet ALWAYS binds to its staged label, and a person
is described once per prompt (the label's definition). The alias table is read off
the plan itself -- the tag's fragments say whose row it quotes -- so a plan written
before this module binds without being rewritten.
"""
from __future__ import annotations

import re

SAID = r"(?:\b(?:[Tt]he|[Aa]n?)\s+[\w'-]+(?:\s+[\w'-]+){0,2}|\b(?:Mr|Mrs|Dr|Miss)\.?\s+[A-Z][\w'-]+)"
TAG = re.compile(rf"(?P<said>{SAID})\s*\((?P<frags>[^()]{{2,300}})\)")
LABELLED = re.compile(r"(<Subject \d+>|<image\d+>)\s*\((?!S\d+\))(?![^()]*\[Shot)[^()]*\)")
"""A parenthetical after a person's label, never a speaker id "(S1)" nor a retention note
"(the man in [Shot 1])" -- those are the grammar's own, not a description."""


def _words(text: str) -> str:
    return " " + " ".join(re.sub(r"[^a-z0-9'-]+", " ", (text or "").lower()).split()) + " "


def tags_in(text: str) -> list[tuple[str, list[str]]]:
    """Every "said (fragment, fragment)" tag in a text, said lower-cased unless a name."""
    out = []
    for m in TAG.finditer(text or ""):
        said = m.group("said")
        said = said if re.match(r"(?:Mr|Mrs|Dr|Miss)\b", said) else said.lower()
        out.append((said, [f.strip() for f in m.group("frags").split(",") if f.strip()]))
    return out


def owner_of(fragments: list[str], rows: dict[str, str]) -> str | None:
    """The one row that says the most of these fragments; None on no match or a tie."""
    counts = {who: sum(_words(f) in _words(words) for f in fragments) for who, words in rows.items()}
    best = max(counts.values(), default=0)
    winners = [w for w, c in counts.items() if c == best]
    return winners[0] if best and len(winners) == 1 else None


def aliases(texts: list[str], rows: dict[str, str]) -> dict[str, list[str]]:
    """{who: [epithet, ...]} over a plan's texts; a phrase two people share binds nobody."""
    seen: dict[str, set[str]] = {}
    for text in texts:
        for said, frags in tags_in(text):
            if (who := owner_of(frags, rows)) is not None:
                seen.setdefault(said.lower(), set()).add(who)
    out: dict[str, list[str]] = {}
    for said, owners in seen.items():
        if len(owners) == 1:
            out.setdefault(next(iter(owners)), []).append(said)
    return out


def bind(text: str, labels: dict[str, str], table: dict[str, list[str]]) -> str:
    """Each staged person's epithets become their label; the epithet's parenthetical goes."""
    for who, label in labels.items():
        for said in sorted(table.get(who, []), key=len, reverse=True):
            pat = rf"(?i)\b{re.escape(said)}\b(?:\s*\([^()]*\))?"
            text = re.sub(pat, label, text)
    return text


def strip_labelled(text: str) -> str:
    """A label is already defined: a parenthetical after one is a second description."""
    return LABELLED.sub(r"\1", text)
