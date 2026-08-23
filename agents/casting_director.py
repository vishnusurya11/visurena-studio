"""Casting director agent — WHO is in each scene (step 02_02).

Names recorded AS WRITTEN ("the detective", "my companion") — canonical ids are
step 03's job. Distinguishes present-in-scene from merely-mentioned.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from agents._crew_common import crew_prompt
from studio import llm

TIER = "workhorse"
SKILL_PATH = Path(__file__).parent / "skills" / "casting_director.md"


class CastMember(BaseModel):
    name_text: str      # as written in the text
    presence: str       # present | mentioned
    role: str           # agent | patient | witness | other
    para_first: int


class SceneCast(BaseModel):
    n: int
    characters: list[CastMember]


class CastReport(BaseModel):
    chapter: int
    scenes: list[SceneCast]


def load_skill() -> str:
    return SKILL_PATH.read_text(encoding="utf-8")


def analyze(chapter: dict, call_sheet, usage: dict | None = None) -> CastReport:
    prompt = crew_prompt(load_skill(), chapter, call_sheet)
    return llm.structured(TIER, prompt, CastReport, usage=usage)
