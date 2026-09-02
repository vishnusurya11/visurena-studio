"""Reference sheets, which belong to the BOOK and not to any one trailer.

The trailer, the song and the episode all draw the same faces from
library/<book>/refs/.  That is the whole point of putting them there: a
character who looks one way in the trailer and another in episode one is two
characters as far as the audience is concerned.

Prompts are built from analysis/, so a reference is answerable to the book --
`profile.physical` is what the text says the person looks like, not what a
model imagined.
"""
from __future__ import annotations

import json
from pathlib import Path

from studio.trailer_spec import RefSheet

STYLE = (
    "Cinematic live-action photograph, anamorphic widescreen, natural film grain, "
    "photoreal, no stylisation, no illustration."
)
SHEET_FRAME = (
    "Full-body character reference on a plain neutral mid-grey backdrop, even soft "
    "studio light, no cast shadows, neutral expression, facing camera, sharp focus, "
    "full figure head to feet in frame."
)
PLATE_FRAME = (
    "Establishing wide plate of an empty location, no people, no figures, "
    "deep focus, even natural light."
)
NO_TYPE = "No text, no lettering, no signage, no watermark, no subtitles."


def character_prompt(physical: str, palette: str) -> str:
    """A reference sheet prompt: house style, sheet framing, then the person."""
    return " ".join([STYLE, palette, SHEET_FRAME, physical.strip(), NO_TYPE])


def location_prompt(described: str, palette: str) -> str:
    """A plate prompt.  Emptiness is stated because a plate with a figure in it
    binds that figure into every shot restaged from it."""
    return " ".join([STYLE, palette, PLATE_FRAME, described.strip(), NO_TYPE])


def physical_of(character: dict) -> str:
    """What the book says this person looks like, or their name as a floor."""
    physical = (character.get("profile") or {}).get("physical") or ""
    return physical.strip() or f"{character.get('name', 'a person')}, period-appropriate dress."


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def ref_id_for(kind: str, entity_id: str) -> str:
    """Stable ref id.  Ids are the join between analysis, plan and job."""
    return f"{'char' if kind == 'character' else 'loc'}-{entity_id}"
