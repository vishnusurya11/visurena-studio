"""Extraction auditor agent — QC over the assembled extraction (step 02_05).

Receives a chapter's full text + its assembled extraction and judges completeness
and faithfulness per dimension. Issues name (chapter, dimension) so the improve
loop can re-run exactly one specialist on one chapter.
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

from agents._crew_common import render_chapter
from studio import llm

TIER = "workhorse"
SKILL_PATH = Path(__file__).parent / "skills" / "extraction_auditor.md"

DIMENSIONS = ("scenes", "time", "characters", "events", "dialogue")


class AuditIssue(BaseModel):
    chapter: int
    scene: int | None = None
    dimension: str      # scenes | time | characters | events | dialogue
    severity: str       # high | low
    note: str


class AuditVerdict(BaseModel):
    ok: bool
    issues: list[AuditIssue]
    summary: str


def load_skill() -> str:
    return SKILL_PATH.read_text(encoding="utf-8")


def audit(chapter: dict, extraction: dict, usage: dict | None = None) -> AuditVerdict:
    prompt = (f"{load_skill()}\n\n--- CHAPTER TEXT ---\n{render_chapter(chapter)}"
              f"\n\n--- EXTRACTION TO AUDIT ---\n"
              f"{json.dumps(extraction, ensure_ascii=False, indent=1)}")
    return llm.structured(TIER, prompt, AuditVerdict, usage=usage)
