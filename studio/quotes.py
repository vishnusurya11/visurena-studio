"""Turn a novel's quoted speech into a line an actor can say. Zero LLM.

Extraction stores `notable_quote` as it appears in the prose, which means it arrives
carrying the narration wrapped around it:

    "It is so," answered John Ferrier.
    "Kiss it and make it well," she said, with perfect gravity, showing the injured
    part up to him. "That's what mother used to do."
    No data yet,

Handed to the screenwriter as source, those get copied through as `verbatim` and printed
under a character cue, where an actor reads "answered John Ferrier" aloud. Three
professional readers hit this independently on the first generated script; one counted
22 speeches carrying attribution tags and 30 ending on an amputated comma.

The comma is the tell: it is the punctuation of `"No data yet," said Holmes` with the
tag cut off. The manner it carried is not recoverable here — that is the screenwriter's
job, as a parenthetical or an action beat — but the comma must not reach the page.
"""

from __future__ import annotations

import re

_OPEN = "\u201c\u2018\""
_CLOSE = "\u201d\u2019\""
_SAID = (r"said|says|answered|answers|asked|asks|cried|cries|replied|replies|"
         r"remarked|remarks|continued|continues|explained|explains|observed|"
         r"exclaimed|shouted|whispered|murmured|added|returned|retorted|gasped")

# A quoted run: "...". Captures what is inside the quotation marks.
_QUOTED = re.compile(f"[{_OPEN}]([^{_OPEN}{_CLOSE}]+)[{_CLOSE}]")
# A trailing attribution outside quotes: `, answered John Ferrier.`
_TRAILING = re.compile(rf"[,;]?\s*(?:{_SAID})\b[^.!?]*[.!?]?\s*$", re.I)
# A leading attribution: `he said, taking a seat,`
_LEADING = re.compile(rf"^\s*(?:he|she|they|[A-Z][a-z]+)\s+(?:{_SAID})\b[^.!?]*", re.I)


def _strip_ends(text: str) -> str:
    return text.strip().strip(_OPEN + _CLOSE).strip()


def _terminate(text: str) -> str:
    """A speech never ends on a comma or a semicolon — that is a severed `said Holmes`."""
    clean = text.rstrip()
    while clean and clean[-1] in ",;:":
        clean = clean[:-1].rstrip()
    if clean and clean[-1] not in ".!?\u2026":
        clean += "."
    return clean


def clean(raw: str) -> str:
    """The spoken words only, punctuated as a line of dialogue.

    Never returns empty for non-empty input: losing a line is worse than a messy one.
    """
    if not raw or not raw.strip():
        return ""
    quoted = _QUOTED.findall(raw)
    if quoted:
        # Prose alternates speech and narration; keep only what is inside the marks.
        text = " ".join(part.strip() for part in quoted if part.strip())
    else:
        text = _strip_ends(raw)
        text = _TRAILING.sub("", text)
        text = _LEADING.sub("", text).lstrip(" ,;")
    text = _terminate(_strip_ends(text))
    return text or _terminate(_strip_ends(raw))


# ---- quote spans with their speaker (craft ruling A9, G-STOLEN) ------------------------------------

_TAG = rf"(?:{_SAID}|says?|thought)"
_SPEECH = re.compile("[“\"]([^“”\"]+)[”\"]")
"""A double-quoted run: a single curly mark is also the apostrophe ("it’s"), so it never bounds speech."""
_AFTER = re.compile(rf"^[\s,;.!?{_CLOSE}]*(?:{_TAG})\s+(?:Mr\.\s+|Mrs\.\s+|Dr\.\s+)?([A-Z][a-z]+|I|he|she)\b"
                    rf"|^[\s,;.!?{_CLOSE}]*(?:Mr\.\s+|Mrs\.\s+|Dr\.\s+)?([A-Z][a-z]+|I|[Hh]e|[Ss]he)\s+(?:{_TAG})\b")
"""The tag after a quote: `," said Mr. Utterson`, `," said I`, `," he asked`."""


def speaker_of(paragraph: str, end: int) -> str:
    """The speaker the tag right after a quote names (lowercased: "utterson", "i", "he"), or ""."""
    hit = _AFTER.search(paragraph[end:end + 60])
    return (hit.group(1) or hit.group(2)).lower() if hit else ""


def quote_spans(paragraphs: list[str]) -> list[tuple[int, str, str]]:
    """(0-based paragraph index, quoted words, speaker or "") for every quoted run of a chapter."""
    return [(k, m.group(1).strip(), speaker_of(p, m.end())) for k, p in enumerate(paragraphs)
            for m in _SPEECH.finditer(p) if m.group(1).strip()]
