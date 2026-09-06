"""The contracts the ten trailer steps hand each other (BLUEPRINT.md).

Each model is one step's OUTPUT.  A gate that is a property of the artifact
alone lives here as a validator, so a step cannot emit something the next
step would have to refuse; gates that need the run (time, a rendered file,
a model's judgment) live in the step and climb its ladder.
"""
from __future__ import annotations

import math
import re
from typing import ClassVar, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from studio.trailer_music import PINNED_DURATION

Register = Literal["elegy", "gothic", "romance", "coming-of-age", "tragedy",
                   "procedural", "detective", "comedy", "adventure"]
VOCAL_REGISTERS = {"elegy", "gothic", "romance", "coming-of-age", "tragedy"}
"""The registers whose thesis a sung refrain can carry; the rest sell the HOW
through spoken lines and a voice would compete (03-music)."""

Function = Literal["hook", "stakes", "threat", "promise", "button", "exposition"]
MAX_THESIS_SYLLABLES = 7
SPEECH_CEILING_PER_100S = 12
"""The top of the dialogue-led trailer norm (8-12 lines per 100 s, see
trailer-sound-chain.md).  `trailer_dialogue.SPOKEN_PER_100S` is the floor."""
MAX_LINES = math.ceil(SPEECH_CEILING_PER_100S * PINNED_DURATION / 100)
"""The most lines a slate may hold: the ceiling rate over the pinned cue.
Run 10's constant 4 sat under the story spine's own floor, so no slate could
ever satisfy it."""
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


QC_TARGETS = {"cuts_on_downbeat": 0.30, "cuts_on_L0": 1.0, "line_over_bed_lu": 5.0,
              "music_only_fraction": 0.45, "longest_music_only_s": 15.0,
              "final_music_only_s": 20.0, "peak_position": (0.78, 0.92),
              "act3_over_act2_lu": 2.0, "pre_title_silence_s": 1.5,
              "title_hit_lu": -25.0, "bed_under_line_lu": -24.0,
              "line_tp": -3.0, "line_crest_db": 10.0,
              "cuts_on_beat_act3": 0.80, "cuts_on_events": 0.90}
"""What the delivered master is asked for.

`cuts_on_beat >= 0.80` across the whole trailer used to be in here, and it is
the single target that FORCED a music video: 76% of run 10's cuts were on the
beat, whole-bar lengths throughout, and a viewer starts counting within four
shots.  It was replaced by two per-act targets pulling opposite ways.  Act 1's is
gone with the beat walk it graded, and so is `on_cap_fraction`, which
measured shots against the walk's act ceilings: the cue's spans now decide
where act 1 cuts, and `cue_cut` grades that.  Act 3's stays --
the locked third act is what an act break sounds like."""


CUE_FLOORS = {"section_changes_cut": 1.0, "cuts_inside_sustain": 0,
              "long_shots_on_sustains": 1.0, "lines_in_troughs": 1.0}
"""What a cut made to its cue cannot miss.  Run 10's master cut inside every
one of its cue's six hold spans and left the section change at 43.0 s inside
a shot; these are floors because a viewer hears each one as a mistake."""


class CueCut(BaseModel):
    """How the delivered cut sits against the cue's own measured events.

    The music-first brick: the cue's spans ARE the shot list, so the report
    grades the picture against the CutMap, never against a bar count the
    pipeline typed.  `None` on the parent report means this was never
    measured, and an unmeasured cut is flagged, never passed.
    """

    cuts_on_events: float = Field(ge=0.0, le=1.0)
    """Share of cuts on a rank >= 2 event within 0.1 s.  Run 10: 0.28, chance 0.11."""
    section_changes_cut: float = Field(ge=0.0, le=1.0)
    cuts_inside_sustain: int = Field(ge=0)
    long_shots_on_sustains: float = Field(ge=0.0, le=1.0)
    """Share of shots over LONG_SHOT that sit on a sustain span."""
    lines_in_troughs: float = Field(ge=0.0, le=1.0)
    accents_cut: float = Field(default=0.0, ge=0.0, le=1.0)
    movement_medians_s: list[float] = Field(default_factory=list)
    """Median shot length per movement: the arc as three numbers."""
    frames_rendered: int = Field(default=0, ge=0)
    frames_played: int = Field(default=0, ge=0)

    @property
    def frames_played_fraction(self) -> float:
        """Picture that reached the master over picture that was rendered;
        the head trim and handle are the tax, everything else is waste."""
        return self.frames_played / self.frames_rendered if self.frames_rendered else 0.0

    def floor_misses(self) -> list[str]:
        out = [k for k in ("section_changes_cut", "long_shots_on_sustains", "lines_in_troughs")
               if getattr(self, k) < CUE_FLOORS[k]]
        if self.cuts_inside_sustain > CUE_FLOORS["cuts_inside_sustain"]:
            out.append("cuts_inside_sustain")
        return out

    def target_misses(self) -> list[str]:
        return ["cuts_on_events"] if self.cuts_on_events < QC_TARGETS["cuts_on_events"] else []


class QCReport(BaseModel):
    """Step 09's reading of the DELIVERED master.  Floor fails; targets flag.

    Run 10 passed every gate here and the owner's verdict was "all I hear is
    music too loud ... it is just some random music .. no dialogues".  Every
    number the old report carried was an AVERAGE -- integrated loudness, true
    peak, a fraction of cuts on a beat -- and a trailer is a SHAPE.  The
    fields below are the shape: where the loudest moment sits, how much of
    the runtime is music with nothing over it, whether act 3 is louder than
    act 2, whether the bed stops before the card or fades into it.
    """

    cuts: int
    cuts_on_beat: float
    cuts_on_downbeat: float
    cuts_on_L0: float
    title_on_downbeat: bool
    integrated_lufs: float
    true_peak: float
    unbound_shots: int
    reused_shots: int = 0
    """Shots playing a take another shot already played.  Run 10 shipped 51
    shots off 25 takes and every gate passed it; the owner watched it and
    said don't reuse, ever."""
    stale_shots: int = 0
    """Shots cut from a clip that is not this plan's own render -- 24% of
    run 10's delivered picture."""
    line_over_bed_lu: list[float] = Field(default_factory=list)
    grid: Literal["metre", "onsets"] = "metre"

    music_only_fraction: float = 0.0
    """Share of the picture that is music with nothing over it.  Run 10: 0.92."""
    longest_music_only_s: float = 0.0
    """The longest such stretch that is NOT the final montage.  Run 10: 40 s."""
    final_music_only_s: float = 0.0
    """The last stretch before the title -- the one the norm lets run to 20 s."""
    speech_occupancy: float = 1.0
    """Share of the picture with a voice on it.  Run 10: 0.021."""
    speech_target: float = 0.0
    """What `speech_occupancy` had to reach, scaled to this trailer's length."""
    peak_position: float = 0.85
    """Where the loudest short-term window sits, as a fraction of the picture.
    Run 10: 0.53, and act 3 was quieter than act 2."""
    act3_over_act2_lu: float = 2.0
    """LU act 3 gains over act 2.  Run 10: -1 to -3."""
    pre_title_silence_s: float = 1.5
    """Seconds under -35 LUFS momentary between the hard out and the hit."""
    hard_out: bool = True
    """Whether the bed STOPPED before the card instead of fading into it."""
    title_hit_lu: float = -20.0
    """How loud the master is where the card is struck.  Run 10's CUE had
    faded to -46 LUFS by then; the field reads the delivered file, which also
    carries the synthesised impact, so what it catches is a hit that never
    reached the master or landed past its end."""
    line_tp: list[float] = Field(default_factory=list)
    """True peak of each levelled line.  Run 10's only line: 0.00 dBFS."""
    line_flat_factor: list[float] = Field(default_factory=list)
    """Runs of identical samples per line -- what clipping leaves.  Run 10: 24.2."""
    line_crest_db: list[float] = Field(default_factory=list)
    """Peak over RMS per line.  Speech runs 12-18 dB; a square wave does not."""
    bed_under_line_lu: list[float] = Field(default_factory=list)
    """The LOUDEST the ducked bed gets under each line, momentary."""
    cuts_on_beat_by_act: list[float] = Field(default_factory=list)
    """On-beat share per act.  One number for the whole trailer cannot tell a
    loose first act from a locked third one, and the difference IS the arc."""
    cue_cut: CueCut | None = None
    """The cut against the cue's measured events; `None` is unmeasured."""

    @property
    def lines_are_clean(self) -> bool:
        """B as safety, not taste: a line that clipped is damage, not a miss."""
        return (all(tp <= QC_TARGETS["line_tp"] for tp in self.line_tp)
                and all(flat == 0.0 for flat in self.line_flat_factor))

    @property
    def floor_pass(self) -> bool:
        return (-15.5 <= self.integrated_lufs <= -12.5 and self.true_peak <= -1.0
                and self.unbound_shots == 0 and self.reused_shots == 0
                and self.stale_shots == 0 and self.lines_are_clean and self.hard_out
                and not (self.cue_cut and self.cue_cut.floor_misses()))

    @property
    def flags(self) -> list[str]:
        """Every target this master missed, by name."""
        return (self._grid_flags() + self._layer_flags() + self._shape_flags()
                + self._line_flags() + self._act_flags() + self._cue_flags())

    def _cue_flags(self) -> list[str]:
        """The cut against its cue: unmeasured is a flag, a missed floor is named."""
        if self.cue_cut is None:
            return ["cue_cut"]
        return self.cue_cut.floor_misses() + self.cue_cut.target_misses()

    def _grid_flags(self) -> list[str]:
        out = [k for k in ("cuts_on_downbeat", "cuts_on_L0") if getattr(self, k) < QC_TARGETS[k]]
        if not self.title_on_downbeat:
            out.append("title_on_downbeat")
        return out + [k for k in ("reused_shots", "stale_shots") if getattr(self, k)]

    def _layer_flags(self) -> list[str]:
        """A: is anybody speaking, and how long does the music run alone."""
        out = [k for k in ("music_only_fraction", "longest_music_only_s",
                           "final_music_only_s") if getattr(self, k) > QC_TARGETS[k]]
        if self.speech_occupancy < self.speech_target:
            out.append("speech_occupancy")
        return out

    def _shape_flags(self) -> list[str]:
        """C and D: where the peak sits and how the trailer ends."""
        low, high = QC_TARGETS["peak_position"]
        out = [] if low <= self.peak_position <= high else ["peak_position"]
        return out + [k for k in ("act3_over_act2_lu", "pre_title_silence_s",
                                  "title_hit_lu") if getattr(self, k) < QC_TARGETS[k]]

    def _line_flags(self) -> list[str]:
        """B: how each line sits against the bed it ducked."""
        out = ["line_over_bed_lu"] if any(
            lu < QC_TARGETS["line_over_bed_lu"] for lu in self.line_over_bed_lu) else []
        if any(lu > QC_TARGETS["bed_under_line_lu"] for lu in self.bed_under_line_lu):
            out.append("bed_under_line_lu")
        if any(crest < QC_TARGETS["line_crest_db"] for crest in self.line_crest_db):
            out.append("line_crest_db")
        return out

    def _act_flags(self) -> list[str]:
        """G: locked in act 3.  Act 1 is the cue's to loosen (`cue_cut`)."""
        if len(self.cuts_on_beat_by_act) < 3:
            return []
        return ["cuts_on_beat_act3"] if self.cuts_on_beat_by_act[2] < QC_TARGETS["cuts_on_beat_act3"] else []
