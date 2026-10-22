"""Two screenplay shadow rows read against the book (craft ruling 2026-10-21, A10 and A11).

ORPHAN-REPLY (A10).  The judges' probe, made the one implementation: a spoken line (dialogue or tale)
that keeps the book's words of a REPLY -- its paragraph follows a paragraph whose quote prompts (ends in
"?", or holds let us / will you / shall we / promise) -- is an orphan when that prompt is in none of the
previous 3 lines and on none of the shots they play on.  Only the first line drawn from a paragraph is
checked.  Jekyll ep01: line 20, "With all my heart, Richard.", answers Enfield's "Let us make a bargain
never to refer to this again", which the plan cut.

PARAGRAPH-HOLE (A11).  The book's speech no line and no source span reaches: a dialogue paragraph (40
words or more, a quote in it) more than half of whose quoted words sit in sentences that share no 4-word
run with any line or span.  Jekyll ep01: 0, 7, 9 ("the very pink of the proprieties"), 13, 15, 21 ("I
can't describe him"), 24, 25 and 26 (the bargain).  A row cites the 0-based list index and the
paragraph's first 8 verbatim words (ruling section 1, fact 1) and is weighted up when the NEXT chapter
uses the dropped sentences' words.  A report: no writer field, nothing refuses.

Both are `fn(plan, paragraphs) -> list` for `scripts/episode/screenplay_replay.py`; a plan is a
plan.json dict or an Episode.  $0, no model.
"""
from __future__ import annotations

import re

from studio import story_layer

LOOKBACK, MATCH = 3, 0.5
"""The probe's numbers: the previous 3 lines; a line keeps a passage when half its words are the passage's."""
PROMPT = re.compile(r"\?\s*$|\blet us\b|\bwill you\b|\bshall we\b|\bpromise\b", re.I)
QUOTE = re.compile("[“\"]([^“”\"]+)[”\"]")
SPOKEN = ("dialogue", "tale")
SMALL = frozenset({"the", "a", "of", "and", "to", "i", "it", "is", "that", "he", "his"})
HOLE_WORDS, HOLE_SHARE = 40, 0.5
SENTENCE = re.compile(r"(?<=[.!?])\s+")


def toks(text: str) -> set[str]:
    return set(re.findall(r"[a-z']+", str(text).lower().replace("’", "'"))) - SMALL


def share(line: str, text: str) -> float:
    """How much of `line`'s words `text` holds (the probe's overlap)."""
    a = toks(line)
    return len(a & toks(text)) / len(a) if a else 0.0


def speech(paragraph: str) -> str:
    """A paragraph's quoted words, or the paragraph when it quotes nobody."""
    return " ".join(QUOTE.findall(paragraph)) or paragraph


def para_of(line: str, paragraphs: list[str]) -> tuple[int, float]:
    """The paragraph whose speech a line keeps most, and how much."""
    best = max(range(len(paragraphs)), key=lambda i: share(line, speech(paragraphs[i])))
    return best, share(line, speech(paragraphs[best]))


def prompt_of(paragraph: str) -> str:
    """The last quote of a paragraph that prompts a reply, or ""."""
    return next((q.strip() for q in reversed(QUOTE.findall(paragraph)) if PROMPT.search(q.strip())), "")


def rows(plan) -> tuple[list[dict], dict[int, list[str]]]:
    """(lines, {shot: its source spans}) of a plan dict or an Episode."""
    shots = plan.get("shots") if isinstance(plan, dict) else getattr(plan, "shots", None)
    spans = {int(_get(s, "index")): list(_get(s, "source") or []) for s in shots or []}
    return story_layer._rows(plan), spans


def _get(row, key):
    return row.get(key) if isinstance(row, dict) else getattr(row, key, None)


# ---- ORPHAN-REPLY -----------------------------------------------------------------------------------

def carried(prompt: str, lines: list[dict], spans: dict[int, list[str]], k: int) -> bool:
    """The prompt is heard in one of the LOOKBACK lines before line k, or shown on a shot they play on."""
    before = lines[max(0, k - LOOKBACK):k]
    shown = [s for shot in {l["shot"] for l in before} | {lines[k]["shot"]} for s in spans.get(int(shot), [])]
    return any(share(prompt, t) >= MATCH for t in [l["text"] for l in before] + shown)


def replies(lines: list[dict], paragraphs: list[str]) -> list[tuple[int, int]]:
    """(line, its paragraph) for the first spoken line drawn from each paragraph past the first."""
    seen, out = set(), []
    for k, line in enumerate(lines):
        if line.get("kind") in SPOKEN and paragraphs:
            i, got = para_of(line["text"], paragraphs)
            if got >= MATCH and i > 0 and i not in seen:
                seen.add(i)
                out.append((k, i))
    return out


def orphan_replies(plan, paragraphs: list[str]) -> list[str]:
    """ORPHAN-REPLY (shadow): every reply whose book prompt the plan neither says nor shows."""
    lines, spans = rows(plan)
    out = []
    for k, i in replies(lines, paragraphs):
        prompt = prompt_of(paragraphs[i - 1])
        if prompt and not carried(prompt, lines, spans, k):
            out.append(f"ORPHAN-REPLY line {lines[k]['index']}: \"{lines[k]['text']}\" answers paragraph {i - 1}'s "
                       f"\"{' '.join(prompt.split()[:8])}\", which no line or shot before it carries -- shadow")
    return out


# ---- PARAGRAPH-HOLE ---------------------------------------------------------------------------------

def sentences(paragraph: str) -> list[str]:
    """The quoted sentences of a paragraph."""
    return [s.strip() for q in QUOTE.findall(paragraph) for s in SENTENCE.split(q) if s.strip()]


def runs(text: str, n: int = 4) -> set[str]:
    words = re.findall(r"[a-z']+", str(text).lower().replace("’", "'"))
    return {" ".join(words[i:i + n]) for i in range(len(words) - n + 1)}


def reached(sentence: str, said: list[str]) -> bool:
    """A line or a source span shares a 4-word run with the sentence (a line keeps the book's words,
    trimmed; a 3-word "Indeed? And what was that?" reaches nothing by sharing two common words)."""
    return any(runs(sentence) & runs(s) for s in said)


def weight(sentence: str, after: str) -> float:
    """1 + the share of the dropped words (content words) the next chapter uses; 1.0 without it."""
    words = story_layer.content_words(sentence)
    return round(1 + len(words & story_layer.content_words(after)) / len(words), 2) if words and after else 1.0


def hole(i: int, paragraph: str, said: list[str], after: str) -> dict | None:
    """The row for paragraph i when more than HOLE_SHARE of its quoted words are unreached, else None."""
    every = sentences(paragraph)
    dropped = [s for s in every if not reached(s, said)]
    total, gone = sum(len(s.split()) for s in every), sum(len(s.split()) for s in dropped)
    if len(paragraph.split()) < HOLE_WORDS or not total or gone / total <= HOLE_SHARE:
        return None
    return {"index": i, "words": " ".join(paragraph.split()[:8]), "unreached": gone, "quoted": total,
            "sentences": dropped, "weight": weight(" ".join(dropped), after)}


def holes(plan, paragraphs: list[str], after: list[str] | None = None) -> list[dict]:
    """Every dialogue paragraph the plan's lines and spans leave mostly unsaid, heaviest first."""
    lines, spans = rows(plan)
    said = [s for found in spans.values() for s in found] + [l["text"] for l in lines]
    found = [hole(i, p, said, " ".join(after or [])) for i, p in enumerate(paragraphs)]
    return sorted([h for h in found if h], key=lambda h: (-h["weight"], h["index"]))


def paragraph_holes(plan, paragraphs: list[str], after: list[str] | None = None) -> list[str]:
    """PARAGRAPH-HOLE (report): one row per hole, the list index and its first 8 verbatim words."""
    return [f"PARAGRAPH-HOLE paragraph {h['index']} ({h['unreached']} of {h['quoted']} quoted words unreached, "
            f"weight {h['weight']}): \"{h['words']}\"" for h in holes(plan, paragraphs, after)]
