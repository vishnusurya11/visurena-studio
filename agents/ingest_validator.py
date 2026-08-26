"""Ingest validator agent — analysis substep 01_05.

Judgment-layer QC over ingest output: reads book.json + per-chapter SAMPLES
(title, first + last paragraph — never the whole book), flags what Python rules
cannot express. Verdict is structured; the caller decides what to do with it
(01_06 improve loop / loud failure).
"""

from __future__ import annotations

import json
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


def _edge(text: str, side: str) -> str:
    """Sample the EDGE that matters: a first paragraph's beginning, a last
    paragraph's ENDING. The sliced side is marked [cut] so the judge never
    mistakes our truncation for the book's (real-run false positive, 2026-08-23)."""
    if len(text) <= _SAMPLE_CHARS:
        return text
    if side == "start":
        return text[:_SAMPLE_CHARS] + " [cut]"
    return "[cut] " + text[-_SAMPLE_CHARS:]


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
        "first_paragraph": _edge(paragraphs[0]["text"], "start") if paragraphs else "",
        "last_paragraph": _edge(paragraphs[-1]["text"], "end") if paragraphs else "",
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
