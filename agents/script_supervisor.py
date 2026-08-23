"""Script supervisor agent — TIME evidence + continuity state changes (step 02_02).

The timeline's raw material is born here: every time phrase recorded VERBATIM,
never interpreted (solving story-time is step 04's job). Also the continuity log:
injuries, possessions, knowledge — film script-supervisor practice.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from agents._crew_common import crew_prompt
from studio import llm

TIER = "workhorse"
SKILL_PATH = Path(__file__).parent / "skills" / "script_supervisor.md"


class TimeEvidence(BaseModel):
    type: str                  # date | time_of_day | duration | recurring | ordering | other
    text: str                  # VERBATIM phrase from the text
    para: int
    anchor: str | None = None  # relative expressions: later/before WHAT (verbatim), or None
    mod: str | None = None     # hedge kept separate: APPROX | MORE_THAN | LESS_THAN | START | MID | END


class StateChange(BaseModel):
    subtype: str     # injury | possession | knowledge | death | relationship | other
    summary: str
    characters: list[str]     # names as written
    para: int
    quote: str                # verbatim evidence


class SceneTime(BaseModel):
    n: int                    # scene number from the call sheet
    time_evidence: list[TimeEvidence]
    state_changes: list[StateChange]


class TimeReport(BaseModel):
    chapter: int
    scenes: list[SceneTime]


def load_skill() -> str:
    return SKILL_PATH.read_text(encoding="utf-8")


def analyze(chapter: dict, call_sheet, usage: dict | None = None) -> TimeReport:
    prompt = crew_prompt(load_skill(), chapter, call_sheet)
    return llm.structured(TIER, prompt, TimeReport, usage=usage)
