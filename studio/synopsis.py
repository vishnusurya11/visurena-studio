"""A 2-3 line scene synopsis, composed deterministically from what extraction found.

WHY THIS LIVES IN `studio/` AND IS CALLED FROM ANALYSIS: a synopsis asserts what the
book says, and analysis is the stage that asserts. It is also computed once per book and
reused by every screenplay target, so buying it per target would be paying repeatedly
for the same sentence.

Zero LLM. The material is already on disk — extraction wrote a one-line scene summary,
a typed event list, and the state changes. The job here is selection and de-duplication,
which is exactly the part that does not need judgment.
"""

from __future__ import annotations

import re

MAX_SENTENCES = 3
_SPLIT = re.compile(r"(?<=[.!?])\s+")
_WORD = re.compile(r"[a-z0-9]+")


def sentences(text: str) -> list[str]:
    return [s for s in _SPLIT.split((text or "").strip()) if s]


def sentence_count(text: str) -> int:
    return len(sentences(text))


def _terminated(text: str) -> str:
    """Extraction summaries do not reliably end in a stop; the synopsis must."""
    clean = (text or "").strip()
    return clean if not clean or clean[-1] in ".!?" else clean + "."


def _key(text: str) -> frozenset:
    """A bag of the first content words — enough to spot a restatement, cheap enough
    to run on every scene of a book."""
    return frozenset(_WORD.findall((text or "").lower())[:8])


def _is_new(candidate: str, seen: list[frozenset], overlap: float = 0.6) -> bool:
    """Is this sentence saying something the synopsis has not already said?"""
    key = _key(candidate)
    if not key:
        return False
    return all(len(key & prior) / len(key) < overlap for prior in seen)


def _texts(items: list[dict], field: str) -> list[str]:
    return [str(item.get(field)) for item in (items or [])
            if isinstance(item, dict) and item.get(field)]


def compose(summary: str, events: list[dict], state_changes: list[dict],
            max_sentences: int = MAX_SENTENCES) -> str:
    """Scene summary, then the events it did not already cover, then a state change.

    Order is the argument: the summary is the most reliable sentence extraction
    produced, events are what happened, and a state change is what it cost.
    """
    picked: list[str] = []
    seen: list[frozenset] = []
    used = 0
    for candidate in [summary, *_texts(events, "summary"), *_texts(state_changes, "change")]:
        line = _terminated(candidate)
        if not line or not _is_new(line, seen):
            continue
        # The cap is on SENTENCES, not on items picked: one event summary can itself be
        # two or three sentences, which is how the real book produced 4-line synopses.
        room = max_sentences - used
        if room <= 0:
            break
        parts = sentences(line)[:room]
        picked.append(" ".join(parts))
        seen.append(_key(line))
        used += len(parts)
    return " ".join(picked)
