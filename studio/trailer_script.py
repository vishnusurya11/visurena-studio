"""The trailer's own screenplay -- the spine every later step is built on.

WHY THIS EXISTS.  Until now the trailer had no script.  It had four judgments
(`story.json`), a list of lines, and a `plan.json` that was the MUSIC's spans
with beats stamped onto them -- so the cue's shape wrote the trailer by
accident.  MEASURED, run 19: the cue's six sections were dealt to the three
movements BY COUNT, section 0 happened to run 0.73 s, and the trailer's first
act was 1% of its 106 s against a 25% share.  No music can rescue a trailer
that never made room for its own first act.

WHY A FILM TRAILER HAS NO SUCH DOCUMENT, AND WHY WE DO.  A trailer house
cannot write a picture column: "you wouldn't want to write a script calling
for scenes and settings that aren't in the negative" (Fred Greene,
entertainment copywriter, UCLA TFT).  Their picture is SEARCHED FOR in footage
that already exists, so the only thing they author is copy -- VO lines and
card text, ten-odd short scripts per trailer, most of which die in the cut.
The trailers that ARE written in advance are the ones whose footage is made to
order: game trailers (Derek Lieu's genre-templated outline) and commercials
(the two-column AV script).  We render every shot, so we are in that second
regime and the picture column is ours to write.

WHAT IT IS NOT.  Not a wish.  Every field is a constraint some later step is
measured against: `seconds` is what the cut must deliver, `movement` is what
the quota is spent in, `line` is what the trailer must SPEAK, `card` is what
the picture holds on.  A beat nobody can honour is refused here, on the page,
before a GPU is asked for anything.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from studio.trailer_edit import MAX_SHOT
from studio.trailer_story import MOVEMENTS, QUOTA_SHARES

Movement = Literal["M1", "M2", "M3"]
Function = Literal["question", "promise", "escalation", "turn", "title", "button"]
"""What a beat is FOR.  The five functions a trailer's spine is made of, plus
the title card that separates the last two."""

RUNTIME = 60.0
RUNTIME_SLACK = 10.0
"""The format, set by the owner 2026-09-07: 60 s, +-10.  Not the 106 s run 19
shipped, and not the 130-148 s of theatrical practice (Redfern n=50, median
142.5 s) -- this is a SOCIAL trailer whose job is to make someone watch the
episode, and the YouTube Shorts feed plays only the first 60 s of any upload."""

FEELINGS = ("calm", "curious", "cold", "urgent", "grieving", "threatening")
"""How a line may be said.  The same vocabulary the voice bank renders a clip
for (`voice_bank.EMOTIONS`), kept here as plain strings so the page contract
does not depend on the audio stack."""


SPEECH_CEILING = 0.50
"""The most of the runtime that may carry a spoken line.  Measured practice is
41-45% for a dialogue-led cut; the ceiling sits just above it so a page is
refused only when it has stopped being a trailer."""

ASPECT = "9:16"
"""The frame it is composed for.  Chosen per book, vertical by default: a
square or a widescreen cut sits letterboxed in the feed the audience is in,
and full-frame 9:16 measured +91% conversion against letterboxed."""

HOLD_CEILING = {"M1": MAX_SHOT, "M2": MAX_SHOT, "M3": MAX_SHOT}
"""What each act may hold one shot for -- the same everywhere.

An earlier draft let the OPENING hold 10 s, on theatrical evidence that an
atmospheric introduction may span three to five bars (BEAT, arXiv 2605.27067).
Social reverses it: ~70% of short-form sessions end before 20% of the video,
multi-scene cutting measured +38% conversion and 5+ scenes +171%, and the first
frame is the hook rather than a build.  A captive theatre audience will wait;
a thumb will not."""


def hold_ceiling(movement: str) -> float:
    """The longest a shot may run in this act."""
    return HOLD_CEILING[movement]


QUOTA_SLACK = 0.08
"""How far a movement's share of the SECONDS may sit from its quota.  Run 19
missed M1's 25% by 24 points; a page that misses by more than this is not the
shape it claims to be."""


class ScriptBeat(BaseModel):
    """One beat of the trailer, written before anything is rendered."""

    id: str = Field(pattern=r"^B\d{2}$")
    movement: Movement
    function: Function
    seconds: float = Field(gt=0.0)
    see: str | None = Field(default=None, description="what the picture shows")
    hear: str | None = Field(default=None, description="what the music and sound do")
    line: str | None = Field(default=None, description="what is spoken over it")
    speaker: str | None = Field(default=None, description="the cast id who speaks it")
    card: str | None = Field(default=None, description="text the picture holds on")
    emotion: str | None = Field(
        default=None,
        description="how the line is said: calm, curious, cold, urgent, grieving, threatening")
    source_scene: int | None = None
    why: str = Field(min_length=4, description="what this beat is for; a beat without one is decoration")

    @property
    def holds(self) -> bool:
        """Whether the picture holds here -- a card, not a shot -- so the
        editor's shot ceiling does not apply."""
        return self.card is not None

    @model_validator(mode="after")
    def _a_line_is_said_some_particular_way(self) -> "ScriptBeat":
        """A spoken beat names its own feeling.

        MEASURED on the first bank run: guessing the emotion from the beat's
        function and reason gave Hope's revenge declaration -- "The hour has
        come when you must answer for the life you took so long before" --
        the GRIEVING read, and gave three of Holmes' deductions URGENT because
        the word "escalation" contains "escalat".  Keyword matching on a
        summary is a story about the beat, not a property of it; the page
        knows what the line is for, so the page says it."""
        if self.emotion and self.emotion not in FEELINGS:
            raise ValueError(f"{self.id}: {self.emotion!r} is not one of {FEELINGS}")
        return self

    @model_validator(mode="after")
    def _a_beat_shows_or_says_something(self) -> "ScriptBeat":
        if not self.see and not self.card:
            raise ValueError(f"{self.id}: a beat must `see` something or hold a card")
        if self.line and not self.speaker:
            raise ValueError(f"{self.id}: a spoken line needs the speaker who says it")
        ceiling = HOLD_CEILING[self.movement]
        if not self.holds and self.seconds > ceiling:
            raise ValueError(f"{self.id}: {self.movement} may hold a shot for {ceiling}s "
                             f"and this beat asks for {self.seconds}s")
        return self


class TrailerScript(BaseModel):
    """The trailer as a page: what happens, in what order, for how long."""

    title: str
    runtime: float = Field(gt=0.0)
    beats: list[ScriptBeat] = Field(min_length=1)
    aspect: str = ASPECT
    genre: str | None = Field(default=None, description="what kind of book, which decides the TYPE")
    kind: str | None = Field(default=None, description="the trailer type the genre calls for")

    @property
    def seconds(self) -> float:
        return round(sum(b.seconds for b in self.beats), 2)

    def movement_seconds(self) -> dict[str, float]:
        """Screen time per movement -- the unit the quota is actually spent in."""
        return {m: round(sum(b.seconds for b in self.beats if b.movement == m), 2)
                for m in MOVEMENTS}

    def movement_shares(self) -> dict[str, float]:
        total = self.seconds or 1.0
        return {m: round(s / total, 3) for m, s in self.movement_seconds().items()}

    def at(self, beat: ScriptBeat) -> float:
        """When a beat starts, in seconds from the first frame."""
        return round(sum(b.seconds for b in self.beats[:self.beats.index(beat)]), 2)

    def share_at(self, beat: ScriptBeat) -> float:
        """Where a beat falls as a share of the runtime.  Position is the one
        structural claim the literature can check and our QC could not see."""
        return round(self.at(beat) / (self.seconds or 1.0), 3)

    def retimed(self, seconds: float) -> "TrailerScript":
        """The same page against a cue of a different length.

        The written seconds are a TARGET, not a promise: two practitioner
        accounts name the audio bed as the structure ("it all starts with the
        audio bed ... we end up filling in picture last" -- Doug Brandt), and
        the fine cut's music "may or may not adhere to the timing of your rough
        cut" (Derek Lieu).  So the cue owns the clock and the page owns the
        PROPORTIONS: every beat is scaled by the same factor, the act shares
        come through untouched, and a scaling that would strand the editor with
        a shot past MAX_SHOT is refused here rather than in the cut."""
        factor = seconds / (self.seconds or 1.0)
        beats = [b.model_copy(update={"seconds": round(b.seconds * factor, 2)}) for b in self.beats]
        return self.model_copy(update={"beats": [ScriptBeat.model_validate(b.model_dump())
                                                 for b in beats], "runtime": seconds})

    def spoken(self) -> list[str]:
        return [b.line for b in self.beats if b.line]

    def speech_seconds(self) -> float:
        return round(sum(b.seconds for b in self.beats if b.line), 2)

    @model_validator(mode="after")
    def _each_movement_gets_its_share_of_the_seconds(self) -> "TrailerScript":
        shares = self.movement_shares()
        for movement in MOVEMENTS:
            off = shares[movement] - QUOTA_SHARES[movement]
            if abs(off) > QUOTA_SLACK:
                raise ValueError(
                    f"{movement} holds {shares[movement]:.0%} of the seconds against its "
                    f"{QUOTA_SHARES[movement]:.0%} share (run 19 shipped M1 at 1%)")
        return self

    @model_validator(mode="after")
    def _it_stops_talking_often_enough_to_be_a_trailer(self) -> "TrailerScript":
        """MEASURED on the first two Scarlet drafts: 72% then 68% of the runtime
        carried a line.  Real trailers run 41-45% even when dialogue-led (one
        measured horror trailer: 41.2%).  Asking in the brief failed twice, so
        the page is refused here and the model is re-asked."""
        share = self.speech_seconds() / (self.seconds or 1.0)
        if share > SPEECH_CEILING:
            raise ValueError(
                f"the page speaks for {share:.0%} of its runtime, past the "
                f"{SPEECH_CEILING:.0%} ceiling; let more beats play on picture and sound")
        return self

    @model_validator(mode="after")
    def _it_runs_the_length_of_the_format(self) -> "TrailerScript":
        if abs(self.seconds - RUNTIME) > RUNTIME_SLACK:
            raise ValueError(f"{self.seconds}s against the format's {RUNTIME}s "
                             f"+-{RUNTIME_SLACK} (the Shorts feed plays 60 s)")
        return self

    @model_validator(mode="after")
    def _the_last_beat_hands_the_viewer_somewhere_to_go(self) -> "TrailerScript":
        """Book trailers' named fatal flaw is ending on a cover with no next
        action.  Every analogue -- podcast trailer, channel trailer, anime PV --
        closes on an explicit one."""
        if not self.beats[-1].card:
            raise ValueError("the last beat must hold a card: the next action")
        return self

    @model_validator(mode="after")
    def _one_title_card_and_it_lands_in_the_last_movement(self) -> "TrailerScript":
        titles = [b for b in self.beats if b.function == "title"]
        if len(titles) != 1:
            raise ValueError(f"a trailer has exactly one title card; this page has {len(titles)}")
        if titles[0].movement != "M3":
            raise ValueError(f"the title card lands in M3, not {titles[0].movement}")
        return self


ACTS = {"M1": "ACT I", "M2": "ACT II", "M3": "ACT III"}


def clock(seconds: float) -> str:
    """m:ss, the way a page is read."""
    return f"{int(seconds // 60)}:{int(seconds % 60):02d}"


def beat_lines(found: ScriptBeat, at: float) -> list[str]:
    """One beat as a person reads it: what it is, then what it carries."""
    out = [f"{found.id}  {clock(at)}  {found.seconds:.1f}s  [{found.function}]"]
    for label, value in (("SEE  ", found.see), ("HEAR ", found.hear), ("CARD ", found.card)):
        if value:
            out.append(f"     {label} {value}")
    if found.line:
        out.append(f"      LINE  {found.speaker}: “{found.line}”")
    out.append(f"      WHY   {found.why}")
    return out


def render(script: TrailerScript) -> str:
    """The script as a page a person can read and argue with."""
    shares = script.movement_shares()
    out = [f"TRAILER — {script.title.upper()}", f"target {clock(script.seconds)}", ""]
    at, seen = 0.0, None
    for found in script.beats:
        if found.movement != seen:
            seen = found.movement
            out += [f"{ACTS[seen]}  —  {clock(at)}  ({shares[seen]:.0%} of the runtime)", ""]
        out += beat_lines(found, at) + [""]
        at += found.seconds
    return "\n".join(out)
