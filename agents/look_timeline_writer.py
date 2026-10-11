"""Look timeline writer -- a character's LOOKS on story time (refs 01_03).

Decision 2026-10-10 (verdict S, fact 2): only WotW's dossiers carry a costume
plot, so the next book would get a single look for everyone.  Every book has
the script supervisor's continuity ledger (`state_changes`, verbatim evidence);
this agent turns it into looks.  Code (`studio.look_timeline`) keeps a non-base
look only when its quote is found in the chapter at 0.85 and writes the table.
"""
from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from studio import llm

TIER = "workhorse"
SKILL_PATH = Path(__file__).parent / "skills" / "look_timeline_writer.md"


class LookRow(BaseModel):
    """One look, flat (a strict provider schema refuses open dicts)."""
    look_id: str
    start_chapter: int = Field(ge=1)
    start_scene: int | None = None
    until_chapter: int | None = None
    until_scene: int | None = None
    headwear: str = ""
    hair: str = ""
    face: str = ""
    top: str = ""
    dirt: str = ""
    quote: str = ""
    quote_chapter: int | None = None


class LookDraft(BaseModel):
    looks: list[LookRow]


def load_skill() -> str:
    return SKILL_PATH.read_text(encoding="utf-8")


def write(dossier: str, usage: dict | None = None, _agent=None) -> LookDraft:
    """The character's looks from its dossier text; `_agent` is the test seam."""
    prompt = f"{load_skill()}\n\n--- THE DOSSIER ---\n{dossier}"
    return llm.structured(TIER, prompt, LookDraft, usage=usage, _agent=_agent)
