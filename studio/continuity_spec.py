"""The continuity contract: a character's LOOKS on story time, a place's MASTERS.

Decision 2026-10-10 (owner): a recurring entity is ONE base picture -- the
character's sheet, the place's master -- and every story-time state is ONE
derivation of that base, recorded in a table keyed by story time.  Never an
edit of an edit; never a composite.  Two files under library/<book>/refs/:

    looks.json    LookBook   -- per character: base look, invariant body, looks, timeline
    places.json   PlaceBook  -- per place: member location ids, masters, states, variants

The judges compare MARKERS in a closed vocabulary, never prose (WotW ep22-27:
the row said "dark brown hair" AND "ash-grey", so no check could fire).
Every path stored here is relative to the book folder.
"""
from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

HEADWEAR = Literal["", "none", "boater", "felt_hat", "bowler", "top_hat", "cap", "bonnet",
                   "helmet", "hood", "bandage", "other_hat"]
HAIR_COLOUR = Literal["", "dark", "brown", "fair", "red", "grey", "white", "bald"]
FACIAL_HAIR = Literal["", "none", "moustache", "beard", "stubble"]
TOP = Literal["", "suit_jacket", "shirt", "shirtless", "coat", "dress", "uniform",
              "nightshirt", "waistcoat", "other"]
DIRT = Literal["", "clean", "dusty", "sooted", "muddy", "bloodied", "wet"]
HARD_MARKERS = ("headwear", "hair_colour", "facial_hair")
"""The markers that lost to the staged sheet in WotW (A §0.2) and that a judge
may refuse on.  `top` and `dirt` stay advisory (verdict S: a VLM does not read
dusty vs sooted reliably at sheet scale)."""

ID = re.compile(r"^[a-z0-9_]+$")
ABSOLUTE = re.compile(r"^(?:[A-Za-z]:[\\/]|[\\/])")
LATE = 10 ** 6
"""The scene number that stands for 'the whole chapter' at an interval's end."""


def relative(path: str) -> str:
    """A stored path is relative to the book folder (CLAUDE.md: never absolute)."""
    if path and ABSOLUTE.match(path):
        raise ValueError(f"{path!r} is absolute; store it relative to the book folder")
    return path


class StoryTime(BaseModel):
    chapter: int = Field(ge=1)
    scene: int | None = Field(default=None, ge=1)

    def opens(self) -> tuple[int, int]:
        return self.chapter, self.scene or 1

    def closes(self) -> tuple[int, int]:
        return self.chapter, self.scene or LATE


class Source(BaseModel):
    chapter: int = Field(ge=1)
    quote: str


class Markers(BaseModel):
    """What a judge checks, in a closed vocabulary; '' is 'not stated'."""
    headwear: HEADWEAR = ""
    hair_colour: HAIR_COLOUR = ""
    facial_hair: FACIAL_HAIR = ""
    top: TOP = ""
    dirt: DIRT = ""


class Layers(BaseModel):
    """The look's words, one layer each; the defining layer is written first."""
    headwear: str = ""
    hair: str = ""
    face: str = ""
    top: str = ""
    dirt: str = ""
    other: str = ""


class Look(BaseModel):
    """One look: its words, its markers, and -- once drawn -- its picture."""
    layers: Layers = Field(default_factory=Layers)
    markers: Markers = Field(default_factory=Markers)
    source: list[Source] = Field(default_factory=list)
    sheet: str = ""
    made_by: Literal["base", "fresh", "edit"] = "fresh"
    parent_sha8: str = ""
    seed: int = 0
    face_change: bool = False

    @field_validator("sheet")
    @classmethod
    def _relative(cls, value: str) -> str:
        return relative(value)


class Span(BaseModel):
    """One interval of story time in one look; `until` None runs to the next span."""
    look: str
    start: StoryTime
    until: StoryTime | None = None

    @model_validator(mode="after")
    def _ordered(self) -> "Span":
        if self.until is not None and self.until.closes() < self.start.opens():
            raise ValueError(f"span of {self.look!r} ends before it starts")
        return self


def overlaps(spans: list[Span]) -> str:
    """The first pair of spans that share story time, as a message, or ''.
    An open span runs until the next one starts, so only a closed span can
    run into its successor (or two spans can start together)."""
    ordered = sorted(spans, key=lambda s: s.start.opens())
    for a, b in zip(ordered, ordered[1:]):
        same = a.start.opens() == b.start.opens()
        runs_into = a.until is not None and a.until.closes() >= b.start.opens()
        if same or runs_into:
            return f"spans {a.look!r} and {b.look!r} overlap"
    return ""


class CharacterLooks(BaseModel):
    base: str
    base_sha8: str = ""
    body: str
    """The invariant body: build, face shape, eyes, skin.  No hair, beard or hat."""
    looks: dict[str, Look]
    timeline: list[Span] = Field(default_factory=list)

    @model_validator(mode="after")
    def _one_base(self) -> "CharacterLooks":
        if self.base not in self.looks:
            raise ValueError(f"the base look {self.base!r} is not defined")
        made_base = [k for k, v in self.looks.items() if v.made_by == "base"]
        if made_base and made_base != [self.base]:
            raise ValueError(f"only the base look {self.base!r} is made_by base, not {made_base}")
        return self

    @model_validator(mode="after")
    def _star(self) -> "CharacterLooks":
        for k, look in self.looks.items():
            if k != self.base and look.parent_sha8 and self.base_sha8 and look.parent_sha8 != self.base_sha8:
                raise ValueError(f"look {k!r} is not one hop from the base sheet "
                                 f"({look.parent_sha8} != {self.base_sha8})")
        return self

    @model_validator(mode="after")
    def _spans(self) -> "CharacterLooks":
        for span in self.timeline:
            if span.look not in self.looks:
                raise ValueError(f"the timeline names {span.look!r}, which is not defined")
        if clash := overlaps(self.timeline):
            raise ValueError(clash)
        return self

    def look_id_at(self, chapter: int, scene: int | None = None) -> str:
        """The look worn at this story time; the base before the first span."""
        point, worn = (chapter, scene or 1), self.base
        for span in sorted(self.timeline, key=lambda s: s.start.opens()):
            if span.start.opens() <= point and (span.until is None or point <= span.until.closes()):
                worn = span.look
        return worn

    def allowed_in(self, chapter: int) -> list[str]:
        """Every look worn at some point of this chapter, in story order: the
        look at each scene where a span starts or ends inside the chapter."""
        points = {1} | {s.start.scene or 1 for s in self.timeline if s.start.chapter == chapter}
        points |= {s.until.scene + 1 for s in self.timeline
                   if s.until is not None and s.until.chapter == chapter and s.until.scene}
        out: list[str] = []
        for scene in sorted(points):
            if (worn := self.look_id_at(chapter, scene)) not in out:
                out.append(worn)
        return out


class LookBook(BaseModel):
    book: str = ""
    characters: dict[str, CharacterLooks] = Field(default_factory=dict)

    def look_id_at(self, who: str, chapter: int, scene: int | None = None) -> str:
        card = self.characters.get(who)
        return card.look_id_at(chapter, scene) if card else ""


class Master(BaseModel):
    master_id: str
    location: str
    view: str
    side: str = ""
    sha8: str = ""
    derived_from: str = ""
    made_by: Literal["fresh", "edit"] = "fresh"


class State(BaseModel):
    state_id: str
    start: StoryTime
    until: StoryTime | None = None
    deltas: list[str] = Field(default_factory=list)
    source: list[Source] = Field(default_factory=list)


class Variant(BaseModel):
    master_id: str
    state_id: str
    view: str
    parent_sha8: str = ""
    sha8: str = ""
    made_by: Literal["edit"] = "edit"


class Place(BaseModel):
    name: str
    members: list[str]
    masters: list[Master] = Field(default_factory=list)
    states: list[State] = Field(default_factory=list)
    variants: list[Variant] = Field(default_factory=list)

    @model_validator(mode="after")
    def _masters_belong(self) -> "Place":
        ids = {m.master_id: m for m in self.masters}
        for m in self.masters:
            if m.location not in self.members:
                raise ValueError(f"master {m.master_id!r} stands in {m.location!r}, not a member")
            if m.derived_from and m.derived_from not in ids:
                raise ValueError(f"master {m.master_id!r} is derived from {m.derived_from!r}, not a master here")
            if m.derived_from and ids[m.derived_from].derived_from:
                raise ValueError(f"master {m.master_id!r} would chain: {m.derived_from!r} is itself derived")
        return self

    @model_validator(mode="after")
    def _variants_one_hop(self) -> "Place":
        ids, states = {m.master_id: m for m in self.masters}, {s.state_id for s in self.states}
        for v in self.variants:
            if v.master_id not in ids:
                raise ValueError(f"variant {v.view!r} names master {v.master_id!r}, not here")
            if v.state_id not in states:
                raise ValueError(f"variant {v.view!r} names state {v.state_id!r}, not here")
            if v.parent_sha8 and ids[v.master_id].sha8 and v.parent_sha8 != ids[v.master_id].sha8:
                raise ValueError(f"variant {v.view!r} is not one hop from its master")
        return self

    def state_at(self, chapter: int, scene: int | None = None) -> str:
        """The place's state at this story time; '' is the master itself."""
        point = (chapter, scene or 1)
        for s in self.states:
            if s.start.opens() <= point and (s.until is None or point <= s.until.closes()):
                return s.state_id
        return ""


class PlaceBook(BaseModel):
    places: dict[str, Place] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _one_place_per_location(self) -> "PlaceBook":
        seen: dict[str, str] = {}
        for pid, place in self.places.items():
            for loc in place.members:
                if loc in seen:
                    raise ValueError(f"{loc!r} belongs to {seen[loc]!r} and {pid!r}; one place each")
                seen[loc] = pid
        return self

    def place_of(self, location: str) -> str:
        return next((pid for pid, p in self.places.items() if location in p.members), "")
