"""Entity resolver agent — canonical characters & locations with coordinates (step 03).

Operates on EXTRACTED surface forms only, never re-reads the book (owner's
extract-first design). Coordinates make the timeline renderable as a map.
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

from studio import llm

TIER = "workhorse"
SKILL_PATH = Path(__file__).parent / "skills" / "entity_resolver.md"


class CanonCharacter(BaseModel):
    id: str
    name: str
    aliases: list[str]
    role: str
    first_chapter: int


class CanonLocation(BaseModel):
    id: str
    name: str
    aliases: list[str]
    region: str
    lat: float
    lon: float
    approximate: bool = False


class CharacterRegistry(BaseModel):
    characters: list[CanonCharacter]


class LocationRegistry(BaseModel):
    locations: list[CanonLocation]


def load_skill() -> str:
    return SKILL_PATH.read_text(encoding="utf-8")


def resolve_characters(observations: list[dict], usage: dict | None = None) -> CharacterRegistry:
    """observations: [{name_text, chapters: [...], sample: "..."}]"""
    prompt = (f"{load_skill()}\n\n--- CHARACTER SURFACE FORMS ---\n"
              f"{json.dumps(observations, ensure_ascii=False)}\n\n"
              f"Return ONLY the characters registry.")
    return llm.structured(TIER, prompt, CharacterRegistry, usage=usage)


def resolve_locations(observations: list[dict], usage: dict | None = None) -> LocationRegistry:
    """observations: [{location_text, chapters: [...], sample: "..."}]"""
    prompt = (f"{load_skill()}\n\n--- LOCATION SURFACE FORMS ---\n"
              f"{json.dumps(observations, ensure_ascii=False)}\n\n"
              f"Return ONLY the locations registry, with coordinates for every entry.")
    return llm.structured(TIER, prompt, LocationRegistry, usage=usage)
