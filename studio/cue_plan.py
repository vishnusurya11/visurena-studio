"""The cue plan: the music's measured spans ARE the shot list.

Three objects.  `CueAsk` is what step 03 asks the music model for, derived
from the frames the render budget affords -- bars split by the story quota,
one event pinned to each section start.  `CuePlan` is what the rendered cue
actually offers once `music_events` has measured it: contiguous spans, each
of a class the picture cuts to in one way.  Every stage downstream of step
03 reads spans from the plan and invents no cut of its own; that is the
whole guarantee that a cut lands where the music has an event.

Design: docs/analysis/research/trailer-music-first.md.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from studio.trailer_edit import MIN_SHOT
from studio.trailer_spec import Movement
from studio.trailer_story import MOVEMENTS, movement_quota

SpanKind = Literal["section", "phrase", "accent", "sustain", "trough", "tail"]

SUSTAIN_BARS = 2.0
"""FLAG: a sustain shorter than this is a phrase.  Typed until a first
music-first master is looked at."""

ACCENT_BEATS = 1.0
"""An accent is an insert on a hit; at two beats it is a phrase."""

MIN_FORM_BARS = 8
"""The shortest register form: an intro of two bars, a build, a stop, a tail."""

EVENT_ORDER = ("pulse_in", "hit", "stop")
"""One landmark per section start, in the order the sections arrive; the
title hit sits after the stop, on the bar the ask names."""


class CueSection(BaseModel):
    """A stretch of the cue at one level, one pulse, one movement."""

    index: int = Field(ge=0)
    start: float = Field(ge=0.0)
    end: float = Field(gt=0.0)
    movement: Movement
    pulse: bool
    level_db: float


class CueSpan(BaseModel):
    """One shot's worth of music, read off the distance to the next event."""

    index: int = Field(ge=0)
    start: float = Field(ge=0.0)
    end: float = Field(gt=0.0)
    kind: SpanKind
    section: int = Field(ge=0)
    movement: Movement
    bars: float = Field(gt=0.0)
    opens_on: str = Field(default="downbeat")
    level_db: float = 0.0
    onset_density: float = Field(default=0.0, ge=0.0)
    rises_db: float = 0.0
    line_room: float = Field(default=0.0, ge=0.0)

    @property
    def seconds(self) -> float:
        return round(self.end - self.start, 3)

    @property
    def beat(self) -> float:
        return self.seconds / self.bars / 4.0 if self.bars else 0.0

    @model_validator(mode="after")
    def _a_span_is_as_long_as_its_kind(self) -> "CueSpan":
        if self.seconds < MIN_SHOT:
            raise ValueError(f"span {self.index}: {self.seconds}s is under MIN_SHOT {MIN_SHOT}")
        if self.kind == "accent" and self.bars * 4.0 > ACCENT_BEATS:
            raise ValueError(f"span {self.index}: an accent longer than a beat is a phrase")
        if self.kind == "sustain" and self.bars < SUSTAIN_BARS:
            raise ValueError(
                f"span {self.index}: a sustain under {SUSTAIN_BARS} bars is a phrase")
        return self


class CuePlan(BaseModel):
    """The rendered cue, measured, as the list of shots it affords."""

    rel_path: str = Field(min_length=1)
    seed: int
    seconds: float = Field(gt=0.0)
    bpm: float = Field(gt=0.0)
    bar: float = Field(gt=0.0)
    sections: list[CueSection] = Field(min_length=1)
    spans: list[CueSpan] = Field(min_length=2)
    hard_out: float = Field(ge=0.0)
    title_hit: float | None = None
    asked: "CueAsk | None" = None

    @model_validator(mode="after")
    def _spans_are_contiguous_over_the_cue(self) -> "CuePlan":
        if self.spans[0].start != 0.0:
            raise ValueError("spans must be contiguous from 0")
        for a, b in zip(self.spans, self.spans[1:]):
            if abs(a.end - b.start) > 1e-6:
                raise ValueError(f"spans must be contiguous: {a.end} then {b.start}")
        if abs(self.spans[-1].end - self.seconds) > 1e-6:
            raise ValueError(f"spans end at {self.spans[-1].end}, cue end is {self.seconds}")
        return self

    @model_validator(mode="after")
    def _every_section_start_is_a_cut(self) -> "CuePlan":
        starts = {round(s.start, 3) for s in self.spans}
        for section in self.sections:
            if round(section.start, 3) not in starts:
                raise ValueError(f"section {section.index} starts at {section.start}s "
                                 f"and the picture does not cut there")
        return self

    @model_validator(mode="after")
    def _movements_never_run_backwards(self) -> "CuePlan":
        order = [MOVEMENTS.index(s.movement) for s in self.spans]
        if any(b < a for a, b in zip(order, order[1:])):
            raise ValueError("movement runs backwards across the spans")
        return self

    @model_validator(mode="after")
    def _the_hard_out_opens_the_tail(self) -> "CuePlan":
        if abs(self.hard_out - self.spans[-1].start) > 1e-6:
            raise ValueError(f"hard_out {self.hard_out} is not the tail start "
                             f"{self.spans[-1].start}")
        if any(a.kind == b.kind == "sustain" for a, b in zip(self.spans, self.spans[1:])):
            raise ValueError("two sustains adjacent: a long shot reads long only "
                             "against a short one")
        return self

    def picture_spans(self) -> list[CueSpan]:
        """Every span the picture fills; the tail is the card's."""
        return [s for s in self.spans if s.kind != "tail"]

    def by_movement(self) -> dict[str, list[CueSpan]]:
        out: dict[str, list[CueSpan]] = {}
        for s in self.picture_spans():
            out.setdefault(s.movement, []).append(s)
        return out


class AskedSection(BaseModel):
    """One section of the ask, in bars, with the texture it should carry."""

    index: int = Field(ge=0)
    bar: int = Field(ge=0)
    bars: int = Field(ge=1)
    movement: Movement
    level: Literal["low", "mid", "high"]
    pulse: bool
    density: Literal["sparse", "building", "dense"]
    cut_unit_beats: float = Field(gt=0.0)


class AskedEvent(BaseModel):
    """A landmark pinned to a bar; `measured` is filled by `verify`."""

    kind: Literal["pulse_in", "hole", "hit", "stop", "title_hit"]
    bar: int = Field(ge=0)
    measured: float | None = None


class CueAsk(BaseModel):
    """What step 03 asks for, derived from the frames the budget affords."""

    bars: int = Field(ge=MIN_FORM_BARS)
    bar: float = Field(gt=0.0)
    bpm: int = Field(gt=0)
    sections: list[AskedSection]
    events: list[AskedEvent]
    title_bar: int = Field(ge=0)

    @property
    def seconds(self) -> float:
        return round(self.bars * self.bar, 3)

    @classmethod
    def for_bars(cls, bars: int, bar: float, bpm: int) -> "CueAsk":
        """Bars split by the story quota, one landmark on each section start."""
        if bars < MIN_FORM_BARS:
            raise ValueError(f"{bars} bars is under the shortest form, {MIN_FORM_BARS} bars")
        sections = sections_for(movement_quota(bars))
        events = [AskedEvent(kind=k, bar=s.bar) for k, s in zip(EVENT_ORDER, sections)]
        title_bar = bars - 2
        events.append(AskedEvent(kind="title_hit", bar=title_bar))
        return cls(bars=bars, bar=bar, bpm=bpm, sections=sections, events=events,
                   title_bar=title_bar)


TEXTURE = {"M1": ("low", False, "sparse", 6.0),
           "M2": ("mid", True, "building", 3.0),
           "M3": ("high", True, "dense", 1.5)}
"""Level, pulse, density and cut unit per movement: the staircase, read as a
table so the caption and the plan cannot drift."""


def sections_for(quota: dict[str, int]) -> list[AskedSection]:
    """The quota laid out as bar-indexed sections in movement order."""
    out, at = [], 0
    for i, m in enumerate(MOVEMENTS):
        level, pulse, density, unit = TEXTURE[m]
        out.append(AskedSection(index=i, bar=at, bars=quota[m], movement=m, level=level,
                                pulse=pulse, density=density, cut_unit_beats=unit))
        at += quota[m]
    return out


CuePlan.model_rebuild()
