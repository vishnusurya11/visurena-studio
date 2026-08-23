"""Profile writer agent — character & location profiles with EVOLUTION (step 05).

Writes from the assembled evidence dossier only (journey, state changes, quotes),
never from the book. Output feeds audiobook casting, image prompts, and song writing.
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

from studio import llm

TIER = "workhorse"
SKILL_PATH = Path(__file__).parent / "skills" / "profile_writer.md"
_MAX_JOURNEY = 40          # cap dossier size sent to the model (cost guard)


class Change(BaseModel):
    chapter: int
    change: str


class CharacterProfile(BaseModel):
    physical: str
    physical_evolution: list[Change]
    mental: str
    mental_evolution: list[Change]
    voice: str
    motivation: str
    arc: str
    role_in_story: str
    inferred_notes: str


class LocationProfile(BaseModel):
    visual: str
    atmosphere: str
    significance: str
    evolution: list[Change]
    sensory: str
    inferred_notes: str


def load_skill() -> str:
    return SKILL_PATH.read_text(encoding="utf-8")


def _trim(dossier: dict) -> dict:
    slim = dict(dossier)
    slim["journey"] = dossier.get("journey", [])[:_MAX_JOURNEY]
    slim["scenes"] = dossier.get("scenes", [])[:_MAX_JOURNEY]
    slim.pop("profile", None)
    return slim


def character_profile(dossier: dict, usage: dict | None = None) -> CharacterProfile:
    prompt = (f"{load_skill()}\n\n--- CHARACTER EVIDENCE DOSSIER ---\n"
              f"{json.dumps(_trim(dossier), ensure_ascii=False)}\n\n"
              f"Write the character profile.")
    return llm.structured(TIER, prompt, CharacterProfile, usage=usage)


def location_profile(dossier: dict, usage: dict | None = None) -> LocationProfile:
    prompt = (f"{load_skill()}\n\n--- LOCATION EVIDENCE DOSSIER ---\n"
              f"{json.dumps(_trim(dossier), ensure_ascii=False)}\n\n"
              f"Write the location profile.")
    return llm.structured(TIER, prompt, LocationProfile, usage=usage)
