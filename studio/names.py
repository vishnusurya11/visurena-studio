"""Surface form -> canonical id. Shared by analysis (step 03) and screenplay (step 01).

This lives in `studio/` rather than inside one step because two stages now resolve the
same names against the same registry, and a second implementation of this matcher is the
most expensive mistake available: the first one shipped a bug that silently mis-assigned
298 of one book's 902 character references, and every test passed the whole time.

Regression suite: tests/test_alias_matching.py.
"""

from __future__ import annotations

import re

_KEEP = re.compile(r"[^a-z0-9 ]+")


def normalize(text: str) -> str:
    """Lowercase, drop punctuation, keep word spacing. The key both sides index on."""
    return _KEEP.sub("", (text or "").lower()).strip()


def run_starts_at(words: list[str], tokens: list[str]) -> bool:
    """Do `tokens` appear as a contiguous run of whole words inside `words`?"""
    span = len(tokens)
    return any(words[i:i + span] == tokens for i in range(len(words) - span + 1))


def match_alias(text: str, index: dict) -> str | None:
    """Exact normalized match, else the longest alias present as WHOLE WORDS.

    Two rules, both learned the hard way in the 2026-08-23 audit:

    1. **Words, not letters.** This did raw substring containment, so "me" matched
       inside "medical", "men" inside "regiment" and "government", and the narrator's
       one-letter alias "i" matched any form containing the letter i. 298 of the book's
       902 character references — a third — were silently assigned to the wrong person.
    2. **A one-word alias only ever matches exactly.** Whole-word matching alone still
       lets "Young" claim "a young girl" and "men" claim "the two men". A single word
       carries too little identity to be recognised inside a phrase it did not write; if
       the form is not the alias, it is somebody else.

    An unmatched form returns None, and that gap is the honest answer — a walk-on
    ("a railway porter") has no canonical identity to find."""
    key = normalize(text)
    if not key:
        return None
    if key in index:
        return index[key]
    words = key.split()
    best = None
    for alias, entity in index.items():
        tokens = alias.split()
        if len(tokens) < 2 or not run_starts_at(words, tokens):
            continue
        if best is None or len(tokens) > best[0]:
            best = (len(tokens), entity)
    return best[1] if best else None


def build_index(entities: list[dict]) -> dict:
    """Normalized name and every alias -> canonical id, for one entity family."""
    index = {}
    for entity in entities:
        for form in [entity["name"], *entity.get("aliases", [])]:
            index[normalize(form)] = entity["id"]
    return index


TITLES = {"mr", "mrs", "miss", "ms", "dr", "doctor", "sir", "lady", "lord",
          "inspector", "sergeant", "constable", "captain", "colonel", "major",
          "reverend", "father", "professor", "madame", "mme", "st"}


def strip_titles(name: str) -> str:
    """Drop leading honorifics. 'Dr. John Watson' -> 'john watson'."""
    words = normalize(name).split()
    while words and words[0] in TITLES:
        words = words[1:]
    return " ".join(words)


def build_surname_index(characters: list[dict]) -> dict:
    """Bare surname and title-less full name -> id, ONLY where unambiguous.

    The registry stores canonical names with titles ('Dr. John Watson') while prose
    says 'Watson', so 160 of 549 dialogue lines lost their speaker on the first real
    run. This closes that gap without reopening the 2026-08-23 substring hole: keys are
    still matched as whole words, and **a key claimed by two characters is dropped
    entirely**. Two Ferriers resolve to neither, because guessing between them is worse
    than the gap.
    """
    claims: dict[str, set] = {}
    for entity in characters:
        bare = strip_titles(entity["name"])
        if not bare:
            continue
        for key in {bare, bare.split()[-1]}:
            claims.setdefault(key, set()).add(entity["id"])
    return {key: next(iter(ids)) for key, ids in claims.items() if len(ids) == 1}
