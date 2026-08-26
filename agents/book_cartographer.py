"""Book cartographer — what are this book's real divisions? (analysis 01_03)

Built because counting stopped working. Five of seven books failed step 01 on one
assumption - that TOC entries and body headings correspond one to one - and each failed
differently. Patching the arithmetic fixed Dracula and immediately broke Metamorphosis,
which is the signature of a wrong model rather than a missing case.

The agent never reads the book. `enumerate_candidates` has already gathered, per heading,
the evidence needed to judge it: the text, the parsed series and ordinal, how many words
of prose follow before the next heading, and whether the TOC anchors to it. Judgment over
gathered evidence is a cheap, well-shaped agent task; re-reading a novel is not.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from studio import llm

TIER = "workhorse"
SKILL_PATH = Path(__file__).parent / "skills" / "book_cartographer.md"

Role = Literal["chapter", "part", "front_matter", "back_matter",
               "contents", "title", "ignore"]

# Only what a judgment needs. The full record carries hrefs and block indices that code
# uses to reassemble the book and that would only be noise in a prompt.
EVIDENCE = ("id", "text", "preview", "words_after", "anchor_resolved",
            "series", "ordinal", "signals")


class Division(BaseModel):
    candidate_id: str
    role: Role
    series: str | None = None          # "chapter" | "letter" | "act" — recorded, not counted
    ordinal: int | None = None         # position among CHAPTERS, 1-based
    reason: str


class MissingDivision(BaseModel):
    """A division the prose contains but the markup never announced as a heading.

    Peter Pan's TOC lists 18 chapters and its body has 17 headings. Reporting 17 is
    wrong and reporting 18 without saying where the 18th is is useless.
    """
    expected_ordinal: int
    inside_candidate_id: str
    evidence: str


class BookMap(BaseModel):
    structure: str                     # one checkable sentence about the book's shape
    divisions: list[Division]
    missing: list[MissingDivision] = Field(default_factory=list)


def load_skill() -> str:
    return SKILL_PATH.read_text(encoding="utf-8")


def brief(candidates: list[dict], toc: list[dict]) -> dict:
    """Evidence only. The TOC is a CLAIM, and is labelled as one in the payload."""
    return {
        "toc_claims": [t.get("title") for t in toc],
        "toc_entry_count": len(toc),
        "headings_found": len(candidates),
        "candidates": [{k: c.get(k) for k in EVIDENCE} for c in candidates],
    }


def chapters(book_map: BookMap) -> list[Division]:
    """The divisions that are chapters, in reading order."""
    return [d for d in book_map.divisions if d.role == "chapter"]


def map_book(candidates: list[dict], toc: list[dict],
             usage: dict | None = None, _agent=None) -> BookMap:
    """One call per book. Returns what each heading is and how many chapters exist.

    `_agent` is the test seam — no test in this repo may call a paid API."""
    prompt = (f"{load_skill()}\n\n--- HEADINGS FOUND, AND WHAT THE TOC CLAIMS ---\n"
              f"{json.dumps(brief(candidates, toc), ensure_ascii=False)}\n\n"
              f"Classify every candidate. The body is the book; the TOC is a claim.")
    return llm.structured(TIER, prompt, BookMap, usage=usage, _agent=_agent)
