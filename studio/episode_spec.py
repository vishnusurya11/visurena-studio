"""The contract of a chapter episode, AUDIO FIRST.

The plan carries no seconds.  Lines are written in order and each names the
shot it plays on; the lines are rendered and MEASURED, and every shot's
length is derived from the audio it carries (`studio/episode_timeline.py`).
So there are no holes: the picture is cut to the voice, never the voice laid
on a picture with gaps (docs/analysis/research/episode-07-audio-first.md).

The brick.  ONE EVENT split by a title card: a TURN (the lead's choice) and a
BUTTON (the world's answer, the last line, never the lead's).  A NARRATOR
carries ~90 % of the speech over cutaways; the few DIALOGUE lines are spoken
ON CAMERA, the speaker's face readable and the lips driven by the line's own
audio.  Only rules computable from the plan live here.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

MIN_SECONDS, MAX_SECONDS = 120.0, 180.0
"""An episode is the WHOLE chapter, two to three minutes (owner, 2026-09-10)."""
WORDS_PER_SECOND = 3.0
"""IndexTTS2 on the cast voices, measured on chapter 1: 33 lines, 147 s of
speech for ~430 words (2026-09-10).  Used only to PROJECT the runtime before
the lines exist; the timeline uses the measured files."""
MAX_WORDS = 18
MAX_BEAT = 1.5
"""The longest silence a shot may name between its lines and the cut."""
MAX_CODA = 4.0
"""The picture after the button, with no voice."""
DIALOGUE_SHARE = (0.05, 0.20)
"""Dialogue words as a share of all words: the 90/10 dial, adjustable."""
MAX_LINES_PER_SHOT = 2
MAX_SPEAKING = 3
MAX_SETUPS = 3
BREATH = 0.35
HANDLE = 0.25
TURN_BAND = (0.50, 0.75)

Section = Literal["hook", "setup", "friction", "payoff", "transition", "turn",
                  "spike", "reaction", "runout", "button", "answer"]
Size = Literal["insert", "extreme_close", "close", "medium_close", "medium", "full", "wide"]
READABLE = {"close", "medium_close"}
"""Where a speaking mouth reads on a phone: a dialogue shot must be one of these."""


class Line(BaseModel):
    index: int = Field(ge=0)
    kind: Literal["dialogue", "narration"]
    speaker: str
    text: str
    shot: int = Field(ge=0)
    """The shot this line plays on.  Lines are in playback order."""

    def words(self) -> int:
        return len(self.text.split())

    def projected_seconds(self) -> float:
        return self.words() / WORDS_PER_SECOND

    @model_validator(mode="after")
    def _short_enough_to_land(self) -> "Line":
        if self.words() > MAX_WORDS:
            raise ValueError(f"line {self.index} is {self.words()} words; the wall is {MAX_WORDS}")
        return self


class Shot(BaseModel):
    index: int = Field(ge=0)
    section: Section
    setup: str
    size: Size
    faces: list[str] = Field(default_factory=list)
    """Whose face is frontal and readable in the panel."""
    frame: str
    motion: str
    take: int = Field(default=0, ge=0)
    beat_s: float = Field(default=0.0, ge=0, le=MAX_BEAT)
    """Named silence after this shot's lines, before the cut."""
    coda_s: float = Field(default=0.0, ge=0, le=MAX_CODA)
    """Picture with no voice at the very end (the world's answer)."""


class Setup(BaseModel):
    described: str
    cast: list[str] = Field(default_factory=list)


class Episode(BaseModel):
    number: int = Field(ge=1)
    title: str
    protagonist: str
    setups: dict[str, Setup]
    shots: list[Shot]
    lines: list[Line]

    # ---- lookups -----------------------------------------------------------
    def shot(self, index: int) -> Shot:
        return next(s for s in self.shots if s.index == index)

    def lines_of(self, shot_index: int) -> list[Line]:
        return [line for line in self.lines if line.shot == shot_index]

    def dialogue(self) -> list[Line]:
        return [line for line in self.lines if line.kind == "dialogue"]

    def button(self) -> Line:
        return self.lines[-1]

    def turn(self) -> Shot:
        return next(shot for shot in self.shots if shot.section == "turn")

    def shot_seconds(self, shot: Shot) -> float:
        carried = self.lines_of(shot.index)
        return (2 * HANDLE + sum(line.projected_seconds() for line in carried)
                + BREATH * max(len(carried) - 1, 0) + shot.beat_s + shot.coda_s)

    def projected_seconds(self) -> float:
        """The runtime before any line is rendered: words at the measured pace,
        breaths, handles, beats and codas."""
        return sum(self.shot_seconds(shot) for shot in self.shots)

    def dialogue_share(self) -> float:
        words = sum(line.words() for line in self.lines) or 1
        return sum(line.words() for line in self.dialogue()) / words

    # ---- the rules ---------------------------------------------------------
    @model_validator(mode="after")
    def _shots_are_in_order_and_named(self) -> "Episode":
        if [s.index for s in self.shots] != list(range(len(self.shots))):
            raise ValueError("shots are numbered 0..n-1 in cut order")
        for shot in self.shots:
            if shot.setup not in self.setups:
                raise ValueError(f"shot {shot.index} names setup {shot.setup!r}, which is not defined")
        if len({s.setup for s in self.shots}) > MAX_SETUPS:
            raise ValueError(f"more than {MAX_SETUPS} setups")
        return self

    @model_validator(mode="after")
    def _lines_are_in_playback_order(self) -> "Episode":
        if not self.lines:
            raise ValueError("an episode with no line has no button")
        if [l.index for l in self.lines] != list(range(len(self.lines))):
            raise ValueError("lines are numbered 0..n-1 in playback order")
        shots = [line.shot for line in self.lines]
        if shots != sorted(shots):
            raise ValueError("a line's shot never precedes an earlier line's shot")
        if any(s >= len(self.shots) for s in shots):
            raise ValueError("a line names a shot that does not exist")
        for shot in self.shots:
            if len(self.lines_of(shot.index)) > MAX_LINES_PER_SHOT:
                raise ValueError(f"shot {shot.index} carries more than {MAX_LINES_PER_SHOT} lines")
            if not self.lines_of(shot.index) and not (shot.beat_s or shot.coda_s):
                raise ValueError(f"shot {shot.index} carries no line and names no beat: a hole")
        return self

    @model_validator(mode="after")
    def _the_shape_is_present(self) -> "Episode":
        sections = [shot.section for shot in self.shots]
        for name in ("hook", "turn", "button"):
            if sections.count(name) != 1:
                raise ValueError(f"an episode has exactly one {name}; found {sections.count(name)}")
        if self.shots[0].section != "hook":
            raise ValueError("the first shot is the hook")
        button = self.button()
        if self.shot(button.shot).section != "button":
            raise ValueError("the last line plays on the button shot")
        if button.speaker == self.protagonist:
            raise ValueError("the last line is not the protagonist's (rule 5)")
        if any(self.lines_of(s.index) for s in self.shots if s.index > button.shot):
            raise ValueError("no line after the button; the coda is picture only")
        if button.shot > 0 and self.shot(button.shot - 1).beat_s < 1.0:
            raise ValueError("the shot before the button names a beat of >= 1.0 s of silence")
        return self

    @model_validator(mode="after")
    def _dialogue_is_on_camera(self) -> "Episode":
        for line in self.dialogue():
            shot = self.shot(line.shot)
            if line.speaker not in shot.faces or shot.size not in READABLE:
                raise ValueError(f"dialogue line {line.index}: shot {shot.index} must show "
                                 f"{line.speaker}'s face at close or medium_close (lips are driven)")
        share = self.dialogue_share()
        if not DIALOGUE_SHARE[0] <= share <= DIALOGUE_SHARE[1]:
            raise ValueError(f"dialogue is {share:.0%} of the words; the dial is "
                             f"{DIALOGUE_SHARE[0]:.0%}-{DIALOGUE_SHARE[1]:.0%}")
        if len({line.speaker for line in self.lines}) > MAX_SPEAKING:
            raise ValueError(f"more than {MAX_SPEAKING} voices")
        return self

    @model_validator(mode="after")
    def _projects_to_an_episode(self) -> "Episode":
        seconds = self.projected_seconds()
        if not MIN_SECONDS <= seconds <= MAX_SECONDS:
            raise ValueError(f"projects to {seconds:.0f} s; an episode is {MIN_SECONDS:.0f}-"
                             f"{MAX_SECONDS:.0f} s (words at {WORDS_PER_SECOND} a second)")
        elapsed, turn_at = 0.0, 0.0
        for shot in self.shots:
            if shot.section == "turn":
                turn_at = elapsed
            elapsed += self.shot_seconds(shot)
        share = turn_at / seconds
        if not TURN_BAND[0] <= share <= TURN_BAND[1]:
            raise ValueError(f"the turn projects to {share:.0%} of the runtime; wanted 50-75 %")
        return self
