"""One beat from one setup: who is in the frame, and how the camera moves.

Selection happens at the ELEMENT level.  A scene is ninety seconds of story and
a trailer shot is two, so choosing scenes gave eleven candidates for thirty-three
shots and every setup appeared three times -- in strict rotation, the same
sequence over and over, which is why the first cuts read as loops.

Step 06 (`scripts/trailer/step_06_plan.py`) is the plan; this module is the
part of it that turns a screenplay setup into a `TrailerBeat` (`beat_of`,
`move_for`) and holds the answer wide (`hold_wide`).  History: this file was
the pre-stage `build_plan.py` CLI, which cut a plan on an onset grid with the
beat walk; that CLI left with BUILD row 55, since no path may invent a cut.
"""
from __future__ import annotations

from studio.shot_grammar import BOUND_FLOOR, MIN_SECONDS, cause_of, destination_of, motivated_move
from studio.trailer_plan import arc_of, movement_for
from studio.trailer_spec import TrailerBeat
from studio.trailer_story import action_text, principal_of


def beat_of(element: dict, index: int, position: float, refs: dict,
            lead: str | None, figure: str | None, movement: str | None = None,
            last: bool = False) -> TrailerBeat:
    """One beat from one action line, cast from WHO IS IN THAT FRAME.

    The subjects are the people the setup's own prose names; the scene cast
    is the fallback for an element that carries none.  Binding on the scene
    cast refused every Utah setup of run 9 for a Mormon somewhere in the
    scene's ninety seconds, and dropped the opposition from the trailer.

    The camera sentence is derived from this beat's own action line, so a beat
    that names nothing photographable gets a locked-off frame rather than the
    twenty-third copy of the same slow push-in.
    """
    subjects = sorted(element.get("subjects", element["cast"]))
    principal = principal_of(subjects, set(refs), lead, figure)
    movement = movement or movement_for(position)
    # The setup's OWN camera term drives the move.  Passing a constant "medium"
    # here made camera_for return "tracks in" for all nine beats, so every take
    # was the same push-in -- and a push-in sampled at four offsets is one image
    # at four focal lengths, which is why 23% of the cut was duplicate frames.
    return TrailerBeat(
        beat_id=f"B{index:02d}", scene_number=element["scene"],
        arc=arc_of(movement, last), movement=movement,
        location_id=element["location_id"], cast=[principal] if principal else [],
        subjects=subjects, image_prompt=action_text(element),
        motion=move_for(element, position))


TERM_MOVE = {"dolly in": ("pushes in", "small"), "handheld": ("follows", "moderate"),
             "rack focus": ("racks focus", "small"), "pan left": ("pans left", "wide"),
             "pan right": ("pans right", "wide"), "tilt up": ("tilts up", "wide"),
             "locked-off": ("static", "")}
"""The screenplay already chose the move; honour it rather than inventing one."""


def move_for(setup: dict, position: float) -> str:
    """This setup's own camera sentence, from the term the adapter wrote."""
    move, amplitude = TERM_MOVE.get(setup.get("term", "locked-off"),
                                    ("pushes in", "small"))
    if move == "static":
        return motivated_move("static", "", "", "", "")
    text = action_text(setup)
    destination = destination_of(text) or "the subject"
    return motivated_move(move, amplitude, "quick" if position >= 0.85 else "slow",
                          cause_of(text), destination)


def hold_wide(sizes: list[str], order: list[str], lengths: list[float],
              reveal) -> list[str]:
    """R4: the answer is never a face filling the frame.

    `choose_sizes` caps a shot carrying a reference at BOUND_FLOOR, so
    "medium" is the WIDEST a bound shot may be -- the man in the room rather
    than his eyes.  A cut too short to read a medium keeps the size the
    grammar chose; an unreadable frame gives nothing away either.
    """
    reveal = set(reveal)
    return [BOUND_FLOOR if beat in reveal and MIN_SECONDS[BOUND_FLOOR] <= length else size
            for size, beat, length in zip(sizes, order, lengths)]
