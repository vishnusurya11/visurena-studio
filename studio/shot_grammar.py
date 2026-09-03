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
                     "and above them; the figure reads as a dark shape, not a face."),
    "wide": ("A wide shot of the whole place, no figure larger than a hand's "
             "width in frame. The horizon crosses the frame at eye height."),
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
    "high": ("The camera looks down from above; the ground fills the background "
             "and no sky is visible."),
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
