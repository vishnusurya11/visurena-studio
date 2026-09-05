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


MODEL_TEXT = (FRAMING, ANGLE)


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
