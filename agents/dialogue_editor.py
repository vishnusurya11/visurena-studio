"""Dialogue editor agent — who speaks to whom (step 02_02).

Notable exchanges with speaker and addressee as written; densest signal for
character voice work later (audiobook narration, character sheets).
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from agents._crew_common import crew_prompt
from studio import llm

TIER = "workhorse"
SKILL_PATH = Path(__file__).parent / "skills" / "dialogue_editor.md"


class Exchange(BaseModel):
    speaker_text: str            # as written; "_group" joint speech; "_unknowable" if truly undeterminable
    addressee_text: str | None
    attribution: str = "implicit"  # explicit | anaphoric | implicit (by referring expression's subject)
    para: int
    notable_quote: str           # verbatim


class SceneDialogue(BaseModel):
    n: int
    exchanges: list[Exchange]


class DialogueReport(BaseModel):
    chapter: int
    scenes: list[SceneDialogue]


def load_skill() -> str:
    return SKILL_PATH.read_text(encoding="utf-8")


def analyze(chapter: dict, call_sheet, usage: dict | None = None) -> DialogueReport:
    prompt = crew_prompt(load_skill(), chapter, call_sheet)
    return llm.structured(TIER, prompt, DialogueReport, usage=usage)
