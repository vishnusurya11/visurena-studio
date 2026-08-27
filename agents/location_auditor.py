"""Location auditor — an independent judge of where a scene happens.

Several judges answer the SAME question about the SAME scene, without seeing each
other's answers or the pipeline's, and the answers are compared. That comparison
measures two different things and both matter:

  * do independent judges AGREE WITH EACH OTHER?  -> is this scene knowable at all
  * do they agree with the PIPELINE?              -> is the pipeline right

A judge shown a proposed answer tends to agree with it, so none is shown one. An
agreement produced by asking "is this right?" measures nothing.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from studio import llm

TIER = "workhorse"
SKILL_PATH = Path(__file__).parent / "skills" / "location_auditor.md"

# Not a location, however often the text says it: a camera cannot stand in a country.
EvidenceKind = Literal["stated_presence", "physical_interaction", "continuity", "named_only"]


class LocationVerdict(BaseModel):
    location_id: str            # a canonical id, or "unlisted", or "ambiguous"
    proposed_name: str | None = None   # required when location_id == "unlisted"
    confidence: Literal["high", "medium", "low"]
    evidence: str               # verbatim words that put the characters there
    evidence_kind: EvidenceKind
    notes: str | None = None


def load_skill() -> str:
    return SKILL_PATH.read_text(encoding="utf-8")


def brief(paragraphs: list[str], locations: list[dict],
          previous_location: str | None = None) -> dict:
    """Source text and the canonical list. No proposed answer, ever.

    `previous_location` is included because continuity is legitimate evidence - a scene
    with no stated departure is still where the story left the characters - but it is
    labelled as the PREVIOUS scene's place, never as a suggestion for this one.
    """
    return {
        "scene_source_text": paragraphs,
        "canonical_locations": [{"id": loc["id"], "name": loc["name"]}
                                for loc in locations],
        "previous_scene_location": previous_location,
    }


def judge(paragraphs: list[str], locations: list[dict],
          previous_location: str | None = None,
          usage: dict | None = None, _agent=None) -> LocationVerdict:
    """One independent judgment. Call it several times for a consensus."""
    prompt = (f"{load_skill()}\n\n--- THE SCENE, VERBATIM FROM THE BOOK ---\n"
              f"{json.dumps(brief(paragraphs, locations, previous_location), ensure_ascii=False)}\n\n"
              f"Where does this scene take place?")
    return llm.structured(TIER, prompt, LocationVerdict, usage=usage, _agent=_agent)
