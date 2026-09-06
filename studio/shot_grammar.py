"""Shot size, angle and motivated camera movement.

Two rules generate everything here.

DURATION BOUNDS SIZE.  A wide frame carries more information than a close-up,
information takes time to read, and the music already decided how much time a
shot has.  So the cut grid SELECTS the legible sizes and the dramatic register
only breaks ties -- which is why a wide at the 85-90% trough reads as a flash
of nothing.

A MOVE IS MOTIVATED WHEN ITS SENTENCE NAMES A CAUSE AND A DESTINATION.  The
previous version chose camera moves from a lookup table keyed on register, and
a table cannot do this: a move with no target is drift by definition, so three
variants of drift is still drift.
"""
from __future__ import annotations

import re

from studio.trailer_story import IMAGE_GATE

LADDER = ("insert", "extreme_close", "close", "medium_close", "medium",
          "full", "wide", "extreme_wide")
"""Smallest to largest by how much of the world is in frame."""

MIN_SECONDS = {"insert": 0.5, "extreme_close": 0.5, "close": 0.7,
               "medium_close": 1.0, "medium": 1.5, "full": 2.0,
               "wide": 2.5, "extreme_wide": 3.0}
"""How long a size needs to be read.  A wide held for 1.35s is unread."""

BOUND_FLOOR = "medium"
"""A shot carrying a character reference must be at least this size.

Below it you have spent a reference sheet, a verbatim physical description and
a seventeen-minute render on twenty pixels of face -- and the binding gate
passes a shot where binding cannot possibly be observed."""

FRAMING = {
    "extreme_wide": ("A single figure stands small and off-centre in the lower "
                     "third of the frame, the whole of the place visible around "
                     "and above them; the figure reads as a dark shape the "
                     "size of a fingernail against the landscape."),
    "wide": ("A wide shot of the whole place, every figure at most a hand's "
             "width tall in frame. The horizon crosses the frame at eye height."),
    "full": ("The full figure stands head to foot within the frame, a hand's "
             "width of air above the head and the feet near the bottom edge."),
    "medium": ("A medium shot cut at the waist; the head fills about a fifth of "
               "the picture height."),
    "medium_close": ("The frame cuts at mid-chest; the head fills about a third "
                     "of the picture height and the eyes sit on the upper third line."),
    "close": ("The frame cuts at the collarbone; the head fills half the picture "
              "height, the eyes on the upper third, the top of the hair just "
              "touching the upper edge."),
    "extreme_close": ("Only the eyes are in frame; the brow crops at the top edge "
                      "and the nose at the bottom."),
    "insert": ("The object fills the middle half of the frame, lit by a single "
               "source, the background soft and out of focus."),
}
"""Crop line first, then fill fraction, then eyeline.

Phrased as an image caption rather than as grip talk, because that is what the
model was trained on.  Never state camera distance -- "an arm's length from her
face" has no caption analogue and is the phrasing that fails."""


def legible_sizes(seconds: float, bound: bool = False) -> list[str]:
    """The sizes a shot of this length can actually hold, largest last."""
    sizes = [s for s in LADDER if MIN_SECONDS[s] <= seconds]
    if bound:
        floor = LADDER.index(BOUND_FLOOR)
        sizes = [s for s in sizes if LADDER.index(s) >= floor] or [BOUND_FLOOR]
    return sizes


def ladder_distance(first: str, second: str) -> int:
    """How many rungs apart two sizes are."""
    return abs(LADDER.index(first) - LADDER.index(second))


ANGLE = {
    "eye": "The lens is level with the eyes; the horizon crosses the frame at eye height.",
    "low": ("The camera sits below his eyeline looking up; the ceiling is visible "
            "behind his head and the horizon sits low in the frame."),
    "high": ("The camera looks down from above; the frame is filled edge to "
             "edge with ground and the tops of things."),
    "profile": "The figure is seen in strict profile, the nose breaking the vertical centre.",
    "overhead": ("The camera looks straight down from directly overhead; the "
                 "ground fills the entire frame."),
}
"""Each angle is stated by its VISIBLE CONSEQUENCE -- what enters or leaves the
background -- because a model trained on image captions has no grip vocabulary.
"Low angle" alone is a term; "the ceiling is visible behind his head" is an
observation, and observations are what these models render toward."""



def motivated_move(move: str, amplitude: str, speed: str, cause: str,
                   destination: str, occluder: str = "") -> str:
    """A camera sentence naming a CAUSE and a DESTINATION.

    An unmotivated drift has three signatures: constant velocity with no settle,
    no referent because the move goes nowhere, and no parallax because near and
    far travel at one rate.  Naming what starts the move and what it arrives at
    fixes the first two; an occluder in the near plane fixes the third.

    The vendor's own worked example carries the destination clause -- "pushes in
    with small amplitude at slow speed toward the folded letter" -- and a lookup
    table keyed on register cannot produce it, which is why three variants of
    drift were still drift.
    """
    if move == "static":
        return "The camera is a static shot, the frame perfectly still, locked off."
    sentence = f"As {cause}, the camera {move} with {amplitude} amplitude at {speed} speed"
    if destination:
        sentence += f" toward {destination}"
    if occluder:
        sentence += f", the edge of {occluder} sliding past the frame"
    return sentence + "."


TROUGH = 0.85
"""Where a released trailer's shots reach their shortest, MEASURED over 50 of
them: 1.50s at the open, 1.33s at the third, 0.54s here.  Size follows, because
a wide held for half a second is a flash of nothing."""


OPENS_AT = "wide"
CLOSES_AT = "extreme_close"
"""The trailer opens wide because the audience has no world yet, and ends tight
because by then the world is known and only the face is new."""


def target_size(position: float) -> float:
    """Where on the ladder this moment wants to sit, as a fractional rung.

    A fractional target rather than an ordering, because an ordering makes the
    chooser oscillate between the two ends of the ladder -- the first version
    produced insert, close, insert, close and called it contrast.  Variation
    has to happen AROUND a moving centre, or it is just alternation.
    """
    top, bottom = LADDER.index(OPENS_AT), LADDER.index(CLOSES_AT)
    return top - (top - bottom) * min(position / TROUGH, 1.0)


def _preference(position: float, bound: bool) -> list[str]:
    """The ladder ordered by distance from where this moment wants to sit."""
    target = target_size(position)
    order = sorted(LADDER, key=lambda s: (abs(LADDER.index(s) - target),
                                          LADDER.index(s)))
    if bound:
        floor = LADDER.index(BOUND_FLOOR)
        order = [s for s in order if LADDER.index(s) <= floor]
    return order


def choose_sizes(lengths: list[float], bound: list[bool],
                 positions: list[float]) -> list[str]:
    """One size per shot: legible for its length, and never twice in a row.

    Three constraints, applied in the order they can fail.  Duration is hard --
    a size that cannot be read in the time available is simply not a candidate.
    Binding is hard too, in the other direction: a shot carrying a character
    reference wider than BOUND_FLOOR spends a sheet on a smudge.  Contrast is
    soft: two rungs apart if the room exists, one rung if it does not, and only
    a repeat is actually refused.
    """
    chosen: list[str] = []
    for seconds, is_bound, position in zip(lengths, bound, positions):
        legible = legible_sizes(seconds, bound=False)
        if is_bound:
            floor = LADDER.index(BOUND_FLOOR)
            legible = [s for s in legible if LADDER.index(s) <= floor]
        if not legible:
            raise ValueError(
                f"no size is legible in {seconds}s; the shortest is "
                f"{min(MIN_SECONDS.values())}s and MIN_SHOT should have caught it")
        wanted = [s for s in _preference(position, is_bound) if s in legible]
        previous = chosen[-1] if chosen else None
        for gap in (2, 1, 0):
            options = [s for s in wanted
                       if previous is None or ladder_distance(s, previous) >= gap]
            if gap == 0:
                options = [s for s in wanted if s != previous] or wanted
            if options:
                chosen.append(options[0])
                break
    return chosen


NOUN_PHRASE = re.compile(
    r"((?:\b(?:a|an|the|his|her|its|their|one)\b\s+)?(?:\w+\s+){0,3}%s)",
    re.I)
"""Article and up to three modifiers before the noun.  'the phial' and 'a small
glass phial' are different pictures, and the adjectives are the difference."""

CLAUSE = re.compile(r"\s+(?:and|then|while|as|before|after)\s+|[,;]\s+", re.I)


def destination_of(text: str) -> str:
    """The photographable thing the sentence lands on.

    The LAST gate noun, not the first: an action line moves from where it starts
    to what it arrives at, and the camera should arrive with it.  "Holmes stoops
    over the body and lifts a small glass phial" ends on the phial.
    """
    matches = list(IMAGE_GATE.finditer(text))
    if not matches:
        return ""
    noun = matches[-1].group(0)
    found = re.search(NOUN_PHRASE.pattern % re.escape(noun), text, re.I)
    return found.group(1).strip() if found else noun


def cause_of(text: str) -> str:
    """The action that starts the move: the clause before the destination."""
    first = CLAUSE.split(text.strip())[0]
    return first.rstrip(" .,;:")


def camera_for(text: str, size: str, position: float) -> str:
    """A camera sentence for this beat, derived from this beat's own action.

    Move, amplitude and speed follow from the size and the place in the arc,
    but the CAUSE and the DESTINATION come out of the book -- which is the
    whole difference between a motivated move and the twenty-three identical
    drifts that shipped.
    """
    destination = destination_of(text)
    if not destination:
        return motivated_move("static", "", "", "", "")
    late = position >= TROUGH
    if size in ("insert", "extreme_close", "close"):
        move, amplitude = "pushes in", "small"
    elif size in ("wide", "extreme_wide"):
        move, amplitude = "cranes slowly down", "wide"
    else:
        move, amplitude = "tracks in", "moderate"
    speed = "quick" if late else "slow"
    return motivated_move(move, amplitude, speed, cause_of(text), destination)


# --- the grammar per span kind -------------------------------------------------
#
# The cue's measured spans ARE the shot list (docs/analysis/research/
# trailer-music-first.md section 5).  A shot's length is read off its span, so
# what is left to decide is HOW each kind of span is filled: a section is the
# widest frame with its reveal on the downbeat; a sustain is one move carrying
# three timed actions; a phrase states one fact; an accent is an insert with
# no face to bind; a trough is a static answer.  `ShotGrammar` is the contract
# that refuses a fill breaking its kind's rule; the functions below produce
# one that passes.

from pydantic import BaseModel, Field, model_validator

from studio.trailer_spec import SpanKind, SpeakerMode, TimedAction

STATIC = motivated_move("static", "", "", "", "")
"""The sentence a locked-off beat carries; a sustain reads it as 'give me a move'."""

FINAL_SECOND = 1.0
"""A sustain's last action lands this far before the cut: the look-up the
next shot answers."""

LOOK_UP = "In the final second the figure looks up, the gaze held to the cut."
INSERT = "An insert: the object alone fills the frame. "
"""Model-facing texts.  Affirmative: each names what the frame holds."""

MODEL_TEXT = (FRAMING, ANGLE, LOOK_UP, INSERT)

PHRASE_SIZE = "medium_close"
"""One fact reads at mid-ladder: it stands apart from the wides around it."""


class ShotGrammar(BaseModel):
    """What a span's kind asks of the shot that fills it."""

    kind: SpanKind
    start: float = Field(ge=0.0)
    end: float = Field(gt=0.0)
    size: str = Field(min_length=1)
    move: str | None = None
    actions: list[TimedAction] = Field(default_factory=list)
    speaker_mode: SpeakerMode | None = None
    reveal_at: float | None = None
    binds_face: bool = False

    @model_validator(mode="after")
    def _actions_sit_inside_the_span_in_order(self) -> "ShotGrammar":
        times = [a.at for a in self.actions]
        if any(not self.start <= t < self.end for t in times):
            raise ValueError(f"{self.kind} at {self.start}s: every action sits inside the span")
        if times != sorted(times):
            raise ValueError(f"{self.kind} at {self.start}s: actions run in time order")
        return self

    @model_validator(mode="after")
    def _a_sustain_carries_one_move_and_three_actions(self) -> "ShotGrammar":
        if self.kind != "sustain":
            return self
        if self.move is None:
            raise ValueError(f"sustain at {self.start}s: a sustain carries one move")
        if len(self.actions) != 3:
            raise ValueError(f"sustain at {self.start}s: three timed actions, "
                             f"got {len(self.actions)}")
        return self

    @model_validator(mode="after")
    def _a_section_reveals_on_its_downbeat(self) -> "ShotGrammar":
        if self.kind == "section" and self.reveal_at != self.start:
            raise ValueError(f"section at {self.start}s: the reveal lands on the "
                             f"downbeat the span opens on, got {self.reveal_at}")
        return self

    @model_validator(mode="after")
    def _a_phrase_states_one_fact(self) -> "ShotGrammar":
        if self.kind == "phrase" and len(self.actions) != 1:
            raise ValueError(f"phrase at {self.start}s: one fact, got {len(self.actions)}")
        return self

    @model_validator(mode="after")
    def _an_accent_is_an_insert_with_no_face(self) -> "ShotGrammar":
        if self.kind == "accent" and (self.binds_face or self.size != "insert"):
            raise ValueError(f"accent at {self.start}s: an insert, and it binds a face "
                             f"or is sized {self.size!r}")
        return self

    @model_validator(mode="after")
    def _a_trough_holds_still(self) -> "ShotGrammar":
        if self.kind == "trough" and self.move is not None:
            raise ValueError(f"trough at {self.start}s: the answer holds still")
        return self


def widest(seconds: float, bound: bool) -> str:
    """The largest size the span can read; a face caps it at BOUND_FLOOR."""
    sizes = legible_sizes(seconds)
    if bound:
        floor = LADDER.index(BOUND_FLOOR)
        sizes = [s for s in sizes if LADDER.index(s) <= floor]
    return sizes[-1]


def size_for(kind: str, seconds: float, bound: bool) -> str:
    """The frame each kind takes: widest for a section, sustain or trough,
    an insert for an accent, mid-ladder for a phrase when it has the time."""
    if kind == "accent":
        return "insert"
    top = widest(seconds, bound)
    if kind == "phrase" and LADDER.index(PHRASE_SIZE) <= LADDER.index(top):
        return PHRASE_SIZE
    return top


def one_move(motion: str, text: str) -> str:
    """The beat's own motivated move, or a slow push toward its destination
    when the beat was locked off: a sustain holds a single move through."""
    if motion != STATIC:
        return motion
    return motivated_move("pushes in", "small", "slow", cause_of(text),
                          destination_of(text) or "the subject")


def timed_actions(start: float, end: float, text: str) -> list[TimedAction]:
    """Open, middle, final-second look-up: the three phases a sustain plays."""
    arrives = destination_of(text) or "the subject"
    return [TimedAction(at=start, phase="open", text=f"{cause_of(text)}."),
            TimedAction(at=round((start + end) / 2.0, 3), phase="middle",
                        text=f"The frame arrives on {arrives}."),
            TimedAction(at=round(end - FINAL_SECOND, 3), phase="final", text=LOOK_UP)]


def speaker_mode_for(cast: list[str], speaker: str | None, spoken: bool) -> SpeakerMode | None:
    """How the face carries the line: two faces share it, the speaker looks
    up on it, a voice with no face is listened to, an absent speaker is heard
    over the shoulder of who is there."""
    if not spoken:
        return None
    if speaker is None:
        return "listening"
    if speaker in cast:
        return "two_shot" if len(cast) >= 2 else "look_up"
    return "ots"


def one_fact(start: float, text: str) -> list[TimedAction]:
    """One visual statement, at the cut."""
    return [TimedAction(at=start, phase="open", text=text)]


def sustain_grammar(span, motion: str, text: str, cast: list[str], spoken: bool,
                    speaker: str | None) -> ShotGrammar:
    """One move, three timed actions, and how the face carries any line."""
    return ShotGrammar(kind="sustain", start=span.start, end=span.end,
                       size=size_for("sustain", span.seconds, bool(cast)), binds_face=bool(cast),
                       move=one_move(motion, text), actions=timed_actions(span.start, span.end, text),
                       speaker_mode=speaker_mode_for(cast, speaker, spoken))


def insert_text(text: str) -> str:
    """The action as an insert: its object alone in frame; a text already
    written as one is kept as it is."""
    if text.startswith(INSERT):
        return text
    return INSERT + (destination_of(text) or text)


def accent_grammar(span, text: str) -> ShotGrammar:
    """An insert on the hit: the action's object alone, no face to bind."""
    return ShotGrammar(kind="accent", start=span.start, end=span.end, size="insert", move=None,
                       actions=one_fact(span.start, insert_text(text)))


def held_grammar(span, motion: str, text: str, cast: list[str], spoken: bool,
                 speaker: str | None) -> ShotGrammar:
    """A section, phrase or trough: one fact; the section's reveal on its
    downbeat; the trough held still with the line it answers."""
    kind = span.kind
    move = None if kind == "trough" or motion == STATIC else motion
    mode = speaker_mode_for(cast, speaker, spoken) if kind == "trough" else None
    return ShotGrammar(kind=kind, start=span.start, end=span.end, move=move,
                       size=size_for(kind, span.seconds, bool(cast)), binds_face=bool(cast),
                       speaker_mode=mode, reveal_at=span.start if kind == "section" else None,
                       actions=one_fact(span.start, text))


def grammar_for(span, motion: str, text: str, cast: list[str], spoken: bool = False,
                speaker: str | None = None) -> ShotGrammar:
    """The fill a span's kind asks for, from the beat's own move and action."""
    if span.kind == "tail":
        raise ValueError("the tail is the card's; the picture fills every other span")
    if span.kind == "sustain":
        return sustain_grammar(span, motion, text, cast, spoken, speaker)
    if span.kind == "accent":
        return accent_grammar(span, text)
    return held_grammar(span, motion, text, cast, spoken, speaker)
