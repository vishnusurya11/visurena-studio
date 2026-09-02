"""The trailer contract.

Two rules are enforced here rather than left to a prompt:

1.  IDENTITY IS BOUND, NOT DESCRIBED.  A shot that shows a character carries
    that character's reference image.  `refs` is not decoration -- `bound()`
    is false when a shot names a cast member it does not carry a ref for, and
    a false `bound()` is a failing shot.  The 2026-08-25 trailer generated
    twelve good reference sheets and then rendered every keyframe
    text-to-image; nothing in the chain ever passed a ref, so no two shots
    showed the same man.

2.  THE MUSIC IS THE TIMELINE.  A shot's duration is not chosen by the shot.
    It is the distance to the next musical event.  `ShotSpec.seconds` is
    derived from the cut grid, never hand-set.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from studio.h3 import NATIVE_H, NATIVE_W, check_canvas

Register = Literal["quiet", "build", "hit", "aftermath"]
"""Where a beat sits in the trailer's dynamic arc, not what it depicts."""


class RefSheet(BaseModel):
    """One reference image belonging to the BOOK, not to any one trailer.

    Characters and locations are the two kinds because they bind differently:
    a character rides `ref_image_1` (identity), a location rides `ref_image_2`
    (place).  Both live under library/<book>/refs/ so the trailer, the song and
    the episode draw on the same faces.
    """

    ref_id: str = Field(min_length=1)
    kind: Literal["character", "location"]
    name: str = Field(min_length=1)
    prompt: str = Field(min_length=1)
    rel_path: str | None = None

    @model_validator(mode="after")
    def _id_is_prefixed(self) -> "RefSheet":
        want = "char-" if self.kind == "character" else "loc-"
        if not self.ref_id.startswith(want):
            raise ValueError(f"{self.kind} ref_id must start with {want!r}: {self.ref_id}")
        return self


class TrailerBeat(BaseModel):
    """One story moment chosen for the trailer, before it becomes a shot.

    `scene_number` points back into screenplay.json so every beat is traceable
    to the script, and through the script to the book.  A beat invented for the
    trailer is not allowed: the trailer sells the book it came from.
    """

    beat_id: str = Field(min_length=1)
    scene_number: int = Field(ge=1)
    arc: Register
    location_id: str = Field(min_length=1)
    cast: list[str] = Field(default_factory=list)
    image_prompt: str = Field(min_length=1)
    motion: str = Field(min_length=1)
    line: str | None = None
    speaker: str | None = None
    emotion: str | None = None

    @model_validator(mode="after")
    def _line_needs_speaker(self) -> "TrailerBeat":
        if self.line and not self.speaker:
            raise ValueError(f"{self.beat_id}: a line needs a speaker")
        if self.speaker and self.speaker not in self.cast:
            raise ValueError(f"{self.beat_id}: speaker {self.speaker!r} not in cast")
        return self


class ShotSpec(BaseModel):
    """A beat once the music has told it how long it is allowed to last."""

    beat_id: str = Field(min_length=1)
    index: int = Field(ge=0)
    start: float = Field(ge=0.0)
    seconds: float = Field(gt=0.0)
    cast: list[str] = Field(default_factory=list)
    char_refs: dict[str, str] = Field(default_factory=dict)
    loc_ref: str | None = None

    def unbound_cast(self) -> list[str]:
        """Characters this shot will show but carries no reference image for.

        Asks what the JOB will carry, never what the prompt says -- a prompt
        naming Holmes is not evidence that Holmes will appear.
        """
        return [c for c in self.cast if c not in self.char_refs]

    def bound(self) -> bool:
        return not self.unbound_cast()

    def ref_slots(self) -> list[str]:
        """Reference ids in H3 ref_image_1..N order: characters, then place."""
        slots = [self.char_refs[c] for c in self.cast if c in self.char_refs]
        if self.loc_ref:
            slots.append(self.loc_ref)
        return slots


class MusicBed(BaseModel):
    """The bed, and the grid of moments the picture is allowed to cut on.

    MiniMax Music 3 sets duration by SECTION COUNT, not by any seconds field
    (comfy_studio finding F11), so `sections` is the real length control and
    `seconds` records what actually came back.
    """

    rel_path: str = Field(min_length=1)
    seconds: float = Field(gt=0.0)
    sections: int = Field(ge=1)
    cuts: list[float] = Field(default_factory=list)

    @model_validator(mode="after")
    def _cuts_are_ordered_and_inside(self) -> "MusicBed":
        if any(b <= a for a, b in zip(self.cuts, self.cuts[1:])):
            raise ValueError("cuts must strictly increase")
        if self.cuts and self.cuts[-1] > self.seconds:
            raise ValueError(f"cut at {self.cuts[-1]}s past bed end {self.seconds}s")
        return self


class TrailerPlan(BaseModel):
    """Everything needed to render one trailer, and nothing about how to."""

    trailer_id: str = Field(min_length=1)
    book_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    kind: Literal["teaser", "main", "character", "tv_spot"] = "main"
    width: int = NATIVE_W
    height: int = NATIVE_H
    fps: int = 24
    refs: list[RefSheet] = Field(default_factory=list)
    beats: list[TrailerBeat] = Field(default_factory=list)
    music: MusicBed | None = None
    shots: list[ShotSpec] = Field(default_factory=list)

    @model_validator(mode="after")
    def _one_canvas_h3_will_honour(self) -> "TrailerPlan":
        """Every shot the same shape, and a shape H3 will not rewrite.

        Mixed aspect ratios were a real bug in the first cut.  Worse, H3's i2v
        path resizes the start frame with crop="disabled" -- a plain stretch --
        so a keyframe at the wrong aspect is distorted and then animated.
        """
        check_canvas(self.width, self.height)
        return self

    def unbound_shots(self) -> list[ShotSpec]:
        return [s for s in self.shots if not s.bound()]
