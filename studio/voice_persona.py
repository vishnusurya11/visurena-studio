"""Writing a Qwen3-TTS VoiceDesign instruction for one character, from the book.

THE CONTRACT IS THE SPEC.  Everything the release post demonstrates and this
repo has measured is enforced here rather than hoped for in a prompt, because
the failures were all silent: a sheet that read well and rendered flat, a cast
that differed on nine attributes and measured as one man.

Two shapes, both official, both emitted:

  BACKGROUND INFORMATION   Character Name / Voice Profile / Background /
                           Presence / Personality.  The default for a
                           character, because REGION goes in Background and
                           BODY goes in Presence, and a voice derived from a
                           life is not a voice averaged from adjectives.

  THE 12-ATTRIBUTE SHEET   gender, pitch, speed, volume, age, clarity,
                           fluency, accent, texture, emotion, tone,
                           personality -- the official names, the official
                           order.  Not `pace`, not `timbre`, not `intonation`.

Three refusals, each of which is a bug the pipeline actually shipped:

  A FLAT SHEET IS REFUSED.  The blog calls it Gradual Control and almost every
  official value uses it -- "Rapid during the laugh, then slowing", "Begins
  conversational, escalates quickly to loud and forceful".  A line has a
  shape; an instruction naming one setting gets one setting back.

  A SHEET WITHOUT A HERTZ ANCHOR IS REFUSED.  Measured on this install: asked
  95/115/85/230, got 95/110/82/241.  It is the only way to place a voice in
  the register on purpose, and casting without one put four men in an 82-110 Hz
  band where 6 of 10 pairs measured above the same-person floor.

  A SHEET WITHOUT AN ACCENT IS REFUSED.  `voice.DELIVERY` refuses to name one
  because naming one drifts American -- but not naming it leaves it GUESSED,
  not unset.
"""
from __future__ import annotations

import re
from typing import Callable

from pydantic import BaseModel, Field, field_validator, model_validator

ATTRIBUTES = ("gender", "pitch", "speed", "volume", "age", "clarity",
              "fluency", "accent", "texture", "emotion", "tone", "personality")
"""The official names in the official order, from the release post's own
example.  `age` sits fifth, after volume -- not beside gender."""

MOVING = ("pitch", "speed", "volume", "emotion", "tone")
"""The attributes that must describe an ARC across the line, not a setting."""

MOVES_AT_LEAST = 3
"""How many of the five must actually move.  Not all five: a character who
holds one register throughout is a legitimate reading, and demanding movement
everywhere would just teach the writer to fake it."""

CHANGE = re.compile(
    r"\b(begin|begins|start|starts|starting|initial|initially|then|after|"
    r"shift|shifts|shifting|transition|transitions|transitioning|rising|rises|"
    r"lowering|lowers|drop|drops|dropping|escalat\w*|accelerat\w*|slowing|"
    r"slows|quicken\w*|building|builds|fading|fades|becomes|moving to|"
    r"gradually|by the end|towards the end|until|once)\b", re.I)

HERTZ = re.compile(r"\b(\d{2,3})\s*hz\b", re.I)
FLOOR_HZ, CEILING_HZ = 60, 320

NATIONALITY = {
    "british": ("british", "england", "english r.p.", "received pronunciation",
                "london", "scottish", "irish", "welsh", "cockney"),
    "american": ("american", "america", "united states", "frontier", "midwest",
                 "southern us", "new york"),
    "other": ("japanese", "chinese", "mandarin", "korean", "german", "french",
              "russian", "spanish", "italian", "portuguese", "indian", "australian"),
}
"""Accent families that must not be mixed in one `accent:` line."""

HEDGE = re.compile(
    r"\b(if required|if needed|only if|where possible|avoid|no specific|"
    r"no strong|not established|unspecified|neutral accent|moderated by|"
    r"influenced by|leaning|somewhat|may be|could be|or possibly|either)\b", re.I)
"""Words that turn a decision into a suggestion.

MEASURED 2026-09-09: Lucy Ferrier's accent came back as "British English
pronunciation, moderated by American frontier vocabulary and rhythm; the text
establishes informal frontier diction but no specific regional accent, so
avoid a strong local dialect" -- two nationalities, a negation and a hedge in
one field.  The render drifted to neither and read as East Asian.  The dossier
names no accent for her, so the writer hedged instead of DECIDING; an accent
the instruction will not commit to is an accent the model picks."""


ORIGIN = re.compile(
    r"[^.;]*\b(?:raised|grew up|born|childhood|schooled|educated|shaped by|"
    r"formed|native|upbringing|from birth|mouth is shaped)\b[^.;]*", re.I)
"""The clauses that claim where a voice was FORMED.

Non-capturing on purpose: `findall` returns the GROUP when there is one, so
a capturing version handed the check the bare word "raised" instead of the
sentence around it, and every rival origin passed.

The accent cross-check reads only these.  A background that mentions a country
the character later travelled to is not a contradiction -- Jefferson Hope is an
American who drives a cab in London, and the first version of this check
refused him for saying so."""

TRIES = 3
"""How many times a refused instruction is asked again before giving up.

The first full run of the cast DIED on character three of twenty-three because
one refusal raised instead of retrying, and the other twenty were never
written.  Unattended means a refusal is a correction, not an ending."""


class NotDirection(ValueError):
    """The instruction says something a microphone cannot capture."""


class VoiceInstruction(BaseModel):
    """One character's voice, in both official shapes."""

    character: str = Field(description="the cast id, e.g. sherlock_holmes")
    name: str = Field(min_length=2, description="the character's name")

    voice_profile: str = Field(
        min_length=120,
        description="the instrument: register, pace, projection, articulation")
    background: str = Field(
        min_length=120,
        description="WHERE THEY ARE FROM, the era, and the work that shaped "
                    "their mouth -- region and nationality as facts of the person")
    presence: str = Field(
        min_length=90,
        description="THE BODY: age, height, build, health, dress, how they carry it")
    personality: str = Field(
        min_length=90, description="how they engage, and what the delivery projects")

    gender: str
    pitch: str = Field(min_length=25)
    speed: str = Field(min_length=20)
    volume: str = Field(min_length=15)
    age: str = Field(min_length=8)
    clarity: str = Field(min_length=12)
    fluency: str = Field(min_length=12)
    accent: str = Field(min_length=10)
    texture: str = Field(min_length=15)
    emotion: str = Field(min_length=15)
    tone: str = Field(min_length=15)
    personality_line: str = Field(min_length=12, alias="personality_attribute")

    model_config = {"populate_by_name": True}

    @field_validator("pitch")
    @classmethod
    def _pitch_names_a_frequency(cls, value: str) -> str:
        """A register you can aim at, not a register you can argue about."""
        found = HERTZ.search(value)
        if not found:
            raise NotDirection(
                "pitch must anchor to a frequency, e.g. 'around 95 Hz'; measured "
                "on this install, an asked hertz comes back within a few Hz")
        hz = int(found.group(1))
        if not FLOOR_HZ <= hz <= CEILING_HZ:
            raise NotDirection(f"{hz} Hz is outside {FLOOR_HZ}-{CEILING_HZ}, "
                               f"which is human speech")
        return value

    @field_validator("accent")
    @classmethod
    def _one_accent_stated_plainly(cls, value: str) -> str:
        """One nationality, no hedging.

        A dossier that never mentions an accent invites the writer to describe
        the absence instead of making the call -- and the model then makes it
        instead, badly."""
        hedged = HEDGE.search(value)
        if hedged:
            raise NotDirection(
                f"accent hedges with {hedged.group(0)!r}: state ONE accent as a "
                f"fact, e.g. 'General American English'. If the book does not "
                f"say, DECIDE from where the character grew up")
        families = {family for family, words in NATIONALITY.items()
                    if any(word in value.lower() for word in words)}
        if len(families) > 1:
            raise NotDirection(
                f"accent mixes {sorted(families)}: name one. Lucy Ferrier was "
                f"cast 'British English ... moderated by American frontier' and "
                f"rendered as neither")
        return value

    @model_validator(mode="after")
    def _the_accent_is_not_argued_with_elsewhere(self) -> "VoiceInstruction":
        """Background may explain the accent; it may not claim a rival ORIGIN.

        Only the origin clauses are read -- "raised in", "grew up", "shaped
        by" -- not every mention of a country.  Jefferson Hope is an American
        who later drives a cab in London, and a check that flagged the word
        "London" anywhere refused a background that was simply true."""
        families = {family for family, words in NATIONALITY.items()
                    if any(word in self.accent.lower() for word in words)}
        if not families:
            return self
        clashing = set()
        for clause in ORIGIN.findall(self.background):
            for family, words in NATIONALITY.items():
                if family not in families and any(w in clause.lower() for w in words):
                    clashing.add(family)
        if clashing:
            raise NotDirection(
                f"accent is {sorted(families)[0]} but Background says this "
                f"person was FORMED in {sorted(clashing)}: where they later "
                f"travelled is fine, where their mouth was shaped is not")
        return self

    @model_validator(mode="after")
    def _the_line_has_a_shape(self) -> "VoiceInstruction":
        """Gradual Control: at least some of the delivery must MOVE.

        The blog's own values almost never sit still -- "Rapid during the
        laugh, then slowing", "shifts abruptly from neutral acceptance to
        intense resentment".  A sheet of fixed settings renders flat, which is
        what every take in the first cast did."""
        moving = [a for a in MOVING if CHANGE.search(getattr(self, a))]
        if len(moving) < MOVES_AT_LEAST:
            raise NotDirection(
                f"only {len(moving)} of {MOVING} describe a change across the "
                f"line ({moving or 'none'}); at least {MOVES_AT_LEAST} must. "
                f"Say what the voice DOES: 'starts level, tightens as he presses'")
        return self

    def hertz(self) -> int:
        """The register this voice was aimed at."""
        return int(HERTZ.search(self.pitch).group(1))

    def sheet(self) -> str:
        """The 12-attribute Acoustic Attribute Control instruction."""
        return "\n".join(
            f"{a}: {getattr(self, 'personality_line' if a == 'personality' else a).rstrip('.')}."
            for a in ATTRIBUTES)

    def persona(self) -> str:
        """The Background Information instruction, the default for a character."""
        return (f"Character Name: {self.name}\n"
                f"Voice Profile: {self.voice_profile}\n"
                f"Background: {self.background}\n"
                f"Presence: {self.presence}\n"
                f"Personality: {self.personality}")

    def instruct(self, shape: str = "persona") -> str:
        """What is actually sent to VoiceDesign."""
        if shape == "sheet":
            return self.sheet()
        if shape == "both":
            return f"{self.persona()}\n\n{self.sheet()}"
        return self.persona()


class Cast(BaseModel):
    """Everyone, and the registers they were placed in."""
    book: str = ""
    voices: list[VoiceInstruction] = Field(default_factory=list)

    def collisions(self, apart: int = 12) -> list[tuple[str, str, int]]:
        """Who was cast too near whom, BEFORE a single clip is rendered.

        A cheap pre-check, not the gate: the gate is a measured resemblyzer
        cosine on the rendered audio, because words differing is not voices
        differing.  This only catches the obvious -- two men put in the same
        few hertz -- so the expensive render is not spent on them."""
        near = []
        for i, one in enumerate(self.voices):
            for other in self.voices[i + 1:]:
                if one.gender.strip().rstrip(".").lower() != other.gender.strip().rstrip(".").lower():
                    continue
                gap = abs(one.hertz() - other.hertz())
                if gap < apart:
                    near.append((one.character, other.character, gap))
        return sorted(near, key=lambda row: row[2])


def dossier_brief(card: dict) -> str:
    """The character as the book recorded them -- the raw material, unedited."""
    profile = card.get("profile", {}) or {}
    parts = [f"NAME: {card.get('name', card.get('id', ''))}",
             f"ROLE: {card.get('role', '')}",
             f"APPEARS: {card.get('appearances', '?')} times, "
             f"from chapter {card.get('first_chapter', '?')}"]
    for field in ("physical", "voice", "mental", "motivation", "arc", "role_in_story"):
        text = (profile.get(field) or "").strip()
        if text:
            parts.append(f"{field.upper()}: {text}")
    quotes = [q.get("quote", "") for q in (card.get("quotes") or [])][:4]
    if quotes:
        parts.append("SAYS: " + " | ".join(q.strip() for q in quotes if q))
    return "\n".join(parts)


def brief(card: dict, setting: str, era: str, hertz: int, taken: dict[str, int],
          texture: str = "") -> str:
    """What the writer is shown: the character, the world, and the slot to hit."""
    others = ", ".join(f"{who} at {hz} Hz" for who, hz in sorted(taken.items(),
                                                                 key=lambda kv: kv[1]))
    return (
        f"Write the Qwen3-TTS VoiceDesign instruction for one character of "
        f"{setting}, {era}.\n\n"
        f"{dossier_brief(card)}\n\n"
        f"THE REGISTER YOU MUST HIT: about {hertz} Hz. This is assigned, not "
        f"chosen — it keeps this voice off every other voice in the cast. Put "
        f"it in `pitch` as a number.\n"
        f"ALREADY CAST: {others or 'nobody yet'}.\n\n"
        f"BACKGROUND INFORMATION is the shape. `Background` carries WHERE THIS "
        f"PERSON IS FROM — region, nationality, the era, and the work that "
        f"shaped their mouth. `Presence` carries THE BODY — age, height, build, "
        f"health, what they wear, how they hold themselves — because a lean "
        f"six-foot man does not resonate like a heavy one, and a man wounded in "
        f"a war does not breathe like a fit one. Take both from the dossier "
        f"above; invent nothing the book contradicts.\n\n"
        f"THE TWELVE ATTRIBUTES use the official names and order: "
        f"{', '.join(ATTRIBUTES)}.\n\n"
        f"EVERY VALUE MUST NAME SOMETHING A MICROPHONE CAN CAPTURE — a "
        f"frequency, a rate, a resonance, a direction of movement. Not "
        f"'sentences arriving already finished'. `personality` as an attribute "
        f"says how it is DELIVERED, never what the character is like.\n\n"
        f"AT LEAST {MOVES_AT_LEAST} OF pitch, speed, volume, emotion, tone MUST "
        f"DESCRIBE A CHANGE ACROSS THE LINE, the way the official examples do: "
        f"'Rapid during the laugh, then slowing to a deliberate pace'; 'Begins "
        f"conversational, escalates quickly to loud and forceful'. A voice that "
        f"holds one setting throughout renders flat.\n\n"
        f"NAME ONE ACCENT, AS A FACT. 'General American English'. 'British "
        f"English, Received Pronunciation.' Nothing else in the field: no "
        f"second nationality, no 'moderated by', no 'if required', no 'avoid a "
        f"strong dialect', no saying the book does not specify one. If the "
        f"dossier never mentions an accent then DECIDE IT from where this "
        f"person grew up and what is written above — a hedged accent is not a "
        f"neutral accent, it is an accent the model chooses instead of you, and "
        f"a frontier girl cast as 'British English moderated by American "
        f"frontier rhythm' rendered as neither. `Background` must give that one "
        f"accent a REASON, and must not name a competing country.")


def refusal_of(why: Exception) -> str:
    """The refusal in the contract's own words, for quoting back."""
    return "; ".join(e.get("msg", "").replace("Value error, ", "")
                     for e in getattr(why, "errors", lambda: [])()) or str(why)


def write(card: dict, setting: str, era: str, hertz: int, taken: dict[str, int],
          model: Callable | None = None, tier: str = "reasoning",
          texture: str = "") -> VoiceInstruction:
    """Draft one character's instruction and hold it to the contract.

    A refusal is quoted back and the instruction asked again, which is what
    every other ladder in this repo does.  The first full cast run raised on
    character three and left twenty uncast."""
    from pydantic import ValidationError

    from studio import llm

    ask = model or llm.structured
    refused = ""
    for _ in range(TRIES):
        text = brief(card, setting, era, hertz, taken, texture)
        try:
            got = ask(tier, "\n\n".join(filter(None, (text, refused))), VoiceInstruction)
            got.character = card.get("id", got.character)
            return got
        except ValidationError as why:
            refused = (f"Your previous instruction was REFUSED: {refusal_of(why)}. "
                       f"Write it again with that fixed.")
    raise NotDirection(f"{card.get('id', 'character')}: {refused}")
