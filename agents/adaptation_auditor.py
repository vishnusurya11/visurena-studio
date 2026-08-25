"""Adaptation auditor — does the scene CONTRADICT the book? (screenplay 05_02)

The highest risk in this stage: on a pipeline whose product is difference, an auditor
tuned to report difference reproduces the 316-violations-nobody-reads failure. The
defence is structural, not rhetorical — an issue whose book_quote fails is_grounded()
against the source paragraphs is dropped before it reaches the improve loop.
"""

from __future__ import annotations

import json
from pathlib import Path

from studio import llm
from studio.screenplay_spec import AuditVerdict

TIER = "workhorse"
SKILL_PATH = Path(__file__).parent / "skills" / "adaptation_auditor.md"


def load_skill() -> str:
    return SKILL_PATH.read_text(encoding="utf-8")


def audit(scene: dict, source_paragraphs: list[str],
          usage: dict | None = None) -> AuditVerdict:
    """One scene against its own source. Contradiction only; never difference."""
    payload = {"scene": scene, "source_paragraphs": source_paragraphs}
    prompt = (f"{load_skill()}\n\n--- ONE DRAFTED SCENE AND ITS SOURCE ---\n"
              f"{json.dumps(payload, ensure_ascii=False)}\n\n"
              f"Return contradictions only. An empty list is the expected result.")
    return llm.structured(TIER, prompt, AuditVerdict, usage=usage)
