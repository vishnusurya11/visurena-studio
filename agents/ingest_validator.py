"""Ingest validator agent — analysis substep 01_05.

Judgment-layer QC over ingest output: reads book.json + per-chapter SAMPLES
(title, first + last paragraph — never the whole book), flags what Python rules
cannot express. Verdict is structured; the caller decides what to do with it
(01_06 improve loop / loud failure).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from pydantic import BaseModel

from studio import llm

TIER = "workhorse"

SKILL_PATH = Path(__file__).parent / "skills" / "ingest_validator.md"


def load_skill() -> str:
    """The checklist prompt lives in a sidecar .md (owner rule: prompts are content,
    not code — editable without touching Python)."""
    return SKILL_PATH.read_text(encoding="utf-8")

_SAMPLE_CHARS = 300  # per paragraph sample — keeps the whole prompt small and cheap


class Issue(BaseModel):
    chapter: int
    kind: str
    severity: str
    note: str


class Verdict(BaseModel):
    ok: bool
    issues: list[Issue]
    summary: str


MAX_SENTENCE = 400       # one runaway sentence must not blow up a per-book prompt
# Split only where a new sentence actually STARTS. Splitting on every [.!?] breaks
# dialogue: `"...?" he asked.` is one sentence, and a lowercase word after a
# closing quote is a speech tag continuing it, not a new sentence beginning.
_SENTENCE_END = re.compile(r'(?<=[.!?])["\'\u201d\u2019)\]]?\s+(?=["\u201c\u2018(]?[A-Z])')


# A period after one of these is an abbreviation, not a sentence end. Peter Pan chapter 2
# was reported as opening with the single word "Mrs." because a capital followed it - a
# sampler that manufactures the damage it is looking for is worse than no sampler.
ABBREVIATIONS = {
    "mr", "mrs", "ms", "dr", "st", "prof", "rev", "hon", "sr", "jr", "capt", "col",
    "gen", "lt", "sgt", "maj", "messrs", "vs", "etc", "cf", "no", "nos", "fig", "vol",
    "ch", "pp", "viz", "approx", "inst", "ult",
}


def _ends_in_abbreviation(text: str) -> bool:
    """Is this fragment's final word an abbreviation rather than a sentence end?

    A single initial counts too: "J. M. Barrie" must not become three sentences.
    """
    word = (text or "").split()[-1] if text.split() else ""
    if not word.endswith("."):
        return False
    stem = word[:-1].strip("\"'“”()")
    return stem.lower() in ABBREVIATIONS or (len(stem) == 1 and stem.isalpha())


def _sentences(text: str) -> list[str]:
    parts = [p for p in _SENTENCE_END.split((text or "").strip()) if p]
    merged: list[str] = []
    for part in parts:
        if merged and _ends_in_abbreviation(merged[-1]):
            merged[-1] = f"{merged[-1]} {part}"      # the split was an abbreviation
        else:
            merged.append(part)
    return merged


def first_sentence(text: str) -> str:
    """The opening sentence, WHOLE.

    The sampler used to send 300 characters with a [cut] marker on the sliced side, and
    three books then failed on boundary verdicts reading "the unmarked ending cannot be
    judged". You cannot ask whether a chapter opens mid-sentence by showing a sentence
    chopped in half - the judged edge must never be our own truncation.
    """
    parts = _sentences(text)
    return parts[0][:MAX_SENTENCE] if parts else ""


def last_sentence(text: str) -> str:
    """The closing sentence, WHOLE. Text that genuinely stops mid-sentence comes back
    stopping mid-sentence, which is the damage this check exists to find."""
    parts = _sentences(text)
    return parts[-1][-MAX_SENTENCE:] if parts else ""


def _sample(chapter: dict) -> dict:
    paragraphs = chapter["paragraphs"]
    return {
        "n": chapter["n"],
        "part": chapter["part"],
        "title": chapter["title"],
        "paragraph_count": len(paragraphs),
        # An empty chapter is legitimate: the n==0 front-matter sentinel is empty for
        # any book that opens straight on Chapter 1. Indexing it unconditionally killed
        # a Frankenstein parse that had already passed every check.
        #
        # WHOLE sentences, never truncations - the edge being judged must be the book's,
        # not ours.
        "opens_with": first_sentence(paragraphs[0]["text"]) if paragraphs else "",
        "ends_with": last_sentence(paragraphs[-1]["text"]) if paragraphs else "",
    }


def build_input(source_dir: Path) -> str:
    """Manifest + per-chapter samples as one compact JSON blob for the prompt."""
    manifest = json.loads((source_dir / "book.json").read_text(encoding="utf-8"))
    samples = []
    for entry in manifest["chapters"]:
        chapter = json.loads(
            (source_dir / entry["file"]).read_text(encoding="utf-8"))
        samples.append(_sample(chapter))
    payload = {"manifest": {k: manifest[k] for k in ("title", "author", "parts", "chapters")},
               "chapter_samples": samples}
    return json.dumps(payload, ensure_ascii=False, indent=1)


def review(source_dir: Path, usage: dict | None = None) -> Verdict:
    """One structured LLM call: the SKILL checklist over the built input.
    Pass `usage={}` to receive token counts back for tracking."""
    prompt = f"{load_skill()}\n\nHere is the ingested book data:\n\n{build_input(source_dir)}"
    return llm.structured(TIER, prompt, Verdict, usage=usage)
