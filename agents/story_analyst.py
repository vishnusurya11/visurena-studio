"""Story analyst agent — EVENTS and actions per scene (step 02_02).

Typed events with participants, paragraph anchors, and a verbatim quote each.
Asserted-realis only (things that actually happen — no plans/fears/hypotheticals).
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from agents._crew_common import crew_prompt
from studio import llm

TIER = "workhorse"
SKILL_PATH = Path(__file__).parent / "skills" / "story_analyst.md"


class Event(BaseModel):
    type: str            # action | movement | perception | reporting | other
    summary: str
    participants: list[str]    # names as written
    paras: list[int]
    quote: str                 # verbatim evidence


class SceneEvents(BaseModel):
    n: int
    events: list[Event]


class EventReport(BaseModel):
    chapter: int
    scenes: list[SceneEvents]


def load_skill() -> str:
    return SKILL_PATH.read_text(encoding="utf-8")


def analyze(chapter: dict, call_sheet, usage: dict | None = None) -> EventReport:
    prompt = crew_prompt(load_skill(), chapter, call_sheet)
    return llm.structured(TIER, prompt, EventReport, usage=usage)
