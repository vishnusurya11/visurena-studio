"""The series map: when the series lets the viewer see a withheld thing (craft ruling 2026-10-21, A12).

One small contract, `library/<book>/series_map.json`, holding only `reveals`: an entity, the episode
and the 0-based chapter paragraph from which its face may be lifted to the camera.  It is NOT the
book-root `series.json`, which already carries the owner's `aspect` (`plan_gates.series_aspect`).  The
Jekyll file is written once, by hand, and the owner reads one page; no agent and no stage write it.
A row cites its paragraph by list index AND its first 8 verbatim words (ruling section 1, fact 1).
"""
from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field, field_validator

FILE = "series_map.json"


class Reveal(BaseModel):
    entity: str = Field(min_length=1)
    episode: int = Field(ge=1)
    """The first episode in which the entity's face may be lifted to the camera."""
    paragraph: int = Field(ge=0)
    """The 0-based list index, in that episode's chapter, from which it may."""
    words: str
    """The paragraph's first 8 verbatim words: a row without them is invalid."""
    why: str = ""

    @field_validator("words")
    @classmethod
    def _verbatim(cls, words: str) -> str:
        if len(words.split()) < 3:
            raise ValueError("a reveal cites its paragraph's first 8 verbatim words")
        return words


class SeriesMap(BaseModel):
    reveals: list[Reveal] = Field(default_factory=list)

    def of(self, entity: str) -> Reveal | None:
        return next((r for r in self.reveals if r.entity == entity), None)


def load(book: Path) -> SeriesMap | None:
    """The book's series map, or None when it has none (a check that needs it cannot read the plan)."""
    path = Path(book) / FILE
    return SeriesMap(**json.loads(path.read_text(encoding="utf-8"))) if path.is_file() else None
