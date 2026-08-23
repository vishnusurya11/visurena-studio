"""Scene breakdown agent — the 1st AD. Cuts one chapter into scenes (step 02_01).

Everyone else on the crew works FROM this call sheet: shared scene numbers,
shared paragraph ranges. Scene boundaries are decided here, once.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from agents._crew_common import crew_prompt
from studio import llm

TIER = "workhorse"
SKILL_PATH = Path(__file__).parent / "skills" / "scene_breakdown.md"


class Frame(BaseModel):
    """Set when a scene is embedded narration (letter, tale, flashback, dream)."""
    type: str                   # flashback | letter | dream | tale
    narrator: str               # who narrates the embedded content
    note: str = ""


class Scene(BaseModel):
    n: int
    para_start: int
    para_end: int
    type: str = "scene"         # scene | nonscene (summary/pause/iterative passages)
    location_text: str          # as written in the text — canonicalization is step 03
    int_ext: str = "UNKNOWN"    # INT | EXT | UNKNOWN
    time_of_day: str = "UNKNOWN"  # DAY | NIGHT | UNKNOWN
    story_day: int | None = None  # in-world day counter within the chapter (1st AD practice)
    frame: Frame | None = None  # embedded-narration flag (diegetic level shift)
    summary: str                # one line, present tense
    boundary_reason: str = ""   # action | character | time | place | level — auditability


class Pov(BaseModel):
    narrator: str               # e.g. "Watson, first person" / "third person"
    tense: str


class CallSheet(BaseModel):
    chapter: int
    pov: Pov
    scenes: list[Scene]


def load_skill() -> str:
    return SKILL_PATH.read_text(encoding="utf-8")


def analyze(chapter: dict, usage: dict | None = None) -> CallSheet:
    prompt = crew_prompt(load_skill(), chapter)
    return llm.structured(TIER, prompt, CallSheet, usage=usage)
