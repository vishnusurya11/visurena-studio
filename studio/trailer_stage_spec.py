"""The contracts the ten trailer steps hand each other (BLUEPRINT.md).

Each model is one step's OUTPUT.  A gate that is a property of the artifact
alone lives here as a validator, so a step cannot emit something the next
step would have to refuse; gates that need the run (time, a rendered file,
a model's judgment) live in the step and climb its ladder.
"""
from __future__ import annotations

import re
from typing import ClassVar, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Register = Literal["elegy", "gothic", "romance", "coming-of-age", "tragedy",
                   "procedural", "detective", "comedy", "adventure"]
VOCAL_REGISTERS = {"elegy", "gothic", "romance", "coming-of-age", "tragedy"}
"""The registers whose thesis a sung refrain can carry; the rest sell the HOW
through spoken lines and a voice would compete (03-music)."""

Function = Literal["hook", "stakes", "threat", "promise", "button", "exposition"]
MAX_THESIS_SYLLABLES = 7
MAX_LINES = 4
PAST = re.compile(r"\b(was|were|had|did|went|came|said|told|knew|saw|took|made)\b", re.I)


def syllables(text: str) -> int:
    """Vowel groups per word, the same heuristic `speech_seconds` uses."""
    return sum(max(1, len(re.findall(r"[aeiouy]+", w))) for w in re.findall(r"[a-z]+", text.lower()))


def proper_nouns(text: str) -> list[str]:
    """Capitalised words that are not sentence-initial."""
    words = text.split()
    return [w for i, w in enumerate(words) if i > 0 and w[:1].isupper()]


class StorySpec(BaseModel):
    """Step 01's output: the derived structure plus the three judged fields."""

    lead: str = Field(min_length=1)
    figure: str = Field(min_length=1)
    turn_scene: int = Field(ge=1)
    resolution_scenes: list[int] = Field(default_factory=list)
    restricted_scenes: list[int] = Field(default_factory=list)
    narrator: str = Field(min_length=1, description="character id or 'omniscient'")
    register_: Register = Field(alias="register")
    thesis: str | None = None
    setting: str = Field(default="", max_length=80,
                         description="period and place in one line, e.g. '1881 London'")
    model_config = ConfigDict(populate_by_name=True, serialize_by_alias=True)

    @property
    def register(self) -> str:
        return self.register_

    @model_validator(mode="after")
    def _thesis_is_a_refrain(self) -> "StorySpec":
        if self.thesis is None:
            return self
        if syllables(self.thesis) > MAX_THESIS_SYLLABLES:
            raise ValueError(f"thesis has {syllables(self.thesis)} syllables; max is 7")
        if proper_nouns(self.thesis):
            raise ValueError(f"thesis names {proper_nouns(self.thesis)}")
        if PAST.search(self.thesis):
            raise ValueError("thesis must be present tense")
        return self

    def vocal_eligible(self) -> bool:
        return self.thesis is not None and self.register_ in VOCAL_REGISTERS


class Slot(BaseModel):
    """Where a line lives.  FOUND: a trough >= 6 dB under the median, held
    >= 1 bar, that the cue has.  MADE: a phrase of the grid the mix ducks
    the bed under (`trailer_dialogue.made_slots`)."""

    start: float = Field(ge=0.0)
    end: float = Field(gt=0.0)
    made: bool = False

    @property
    def seconds(self) -> float:
        return self.end - self.start


class Metre(BaseModel):
    """Step 03's measurement of one rendered seed."""

    seed: int
    rel_path: str = Field(min_length=1)
    seconds: float = Field(gt=0.0)
    bpm: float = Field(gt=0.0)
    bar: float = Field(gt=0.0)
    beats_per_bar: int = 4
    beats: list[float]
    downbeats: list[float]
    bars_in_mode: float = Field(ge=0.0, le=1.0)
    grid: Literal["metre", "onsets"]
    fitness: float
    hits: list[float] = Field(default_factory=list)
    stopdowns: list[float] = Field(default_factory=list)
    phrase_starts: list[float] = Field(default_factory=list)
    title_hit: float | None = None
    slots: list[Slot] = Field(default_factory=list)

    METRIC_FLOOR: ClassVar[float] = 0.65

    @property
    def beat(self) -> float:
        return round(self.bar / self.beats_per_bar, 4)

    @model_validator(mode="after")
    def _grid_is_consistent(self) -> "Metre":
        if any(b <= a for a, b in zip(self.beats, self.beats[1:])):
            raise ValueError("beats must strictly increase")
        if not set(self.downbeats) <= set(self.beats):
            raise ValueError("every downbeat must be a beat")
        if self.grid == "metre" and self.bars_in_mode < self.METRIC_FLOOR:
            raise ValueError(f"bars_in_mode {self.bars_in_mode} is rubato; grid must be onsets")
        for slot in self.slots:
            if slot.seconds < self.bar:
                raise ValueError(f"slot {slot.start}-{slot.end} is shorter than a bar")
        return self


class SlateLine(BaseModel):
    text: str = Field(min_length=1)
    speaker: str | None = None
    function: Function
    kept: bool = False
    bold: bool = False
    pool: str = Field(min_length=1)
    score: float
    window: Slot | None = Field(default=None, description=(
        "the window the orderer chose this line for; None on a pool line"))

    @property
    def card(self) -> bool:
        return self.speaker is None

    @property
    def words(self) -> int:
        return len(self.text.split())


class LineSlate(BaseModel):
    """Step 04's output, in trailer order: hook -> answer -> threat -> (title) -> button."""

    lines: list[SlateLine] = Field(default_factory=list, max_length=MAX_LINES)
    iconicity: Literal["full", "thin", "none"]
    music_only: bool = False
    pool: list[SlateLine] = Field(default_factory=list, description=(
        "labelled candidates the slate did not use; step 05's next-line-same-function rung"))

    @model_validator(mode="after")
    def _a_slate_must_ask_and_threaten(self) -> "LineSlate":
        if self.music_only:
            return self
        functions = {l.function for l in self.lines}
        if "hook" not in functions or not functions & {"threat", "stakes"}:
            raise ValueError("a slate needs a hook and a threat or stakes, or music_only")
        return self

    def spoken(self) -> list[SlateLine]:
        return [l for l in self.lines if not l.card]


class VoiceLine(BaseModel):
    """Step 05's output per line: a file and what was MEASURED from it."""

    index: int = Field(ge=0)
    text: str
    speaker: str | None
    rel_path: str | None = None
    seconds: float | None = None
    similarity: float | None = None
    seed: int | None = None
    card: bool = False


QC_TARGETS = {"cuts_on_beat": 0.80, "cuts_on_downbeat": 0.30, "cuts_on_L0": 1.0,
              "on_cap_fraction": 0.10, "line_over_bed_lu": 5.0}


class QCReport(BaseModel):
    """Step 09's reading of the DELIVERED master.  Floor fails; targets flag."""

    cuts: int
    cuts_on_beat: float
    cuts_on_downbeat: float
    cuts_on_L0: float
    on_cap_fraction: float
    title_on_downbeat: bool
    integrated_lufs: float
    true_peak: float
    unbound_shots: int
    line_over_bed_lu: list[float] = Field(default_factory=list)
    grid: Literal["metre", "onsets"] = "metre"

    @property
    def floor_pass(self) -> bool:
        return (-15.5 <= self.integrated_lufs <= -12.5 and self.true_peak <= -1.0
                and self.unbound_shots == 0)

    @property
    def flags(self) -> list[str]:
        out = [k for k in ("cuts_on_beat", "cuts_on_downbeat", "cuts_on_L0")
               if getattr(self, k) < QC_TARGETS[k]]
        if self.on_cap_fraction > QC_TARGETS["on_cap_fraction"]:
            out.append("on_cap_fraction")
        if not self.title_on_downbeat:
            out.append("title_on_downbeat")
        if any(lu < QC_TARGETS["line_over_bed_lu"] for lu in self.line_over_bed_lu):
            out.append("line_over_bed_lu")
        return out
