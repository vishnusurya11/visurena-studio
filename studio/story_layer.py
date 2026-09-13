"""The story layer: the one question an episode answers, and the value each
shot turns.

Both rules come from the screenwriting craft, read 2026-09-12, and both explain
faults we had already measured without knowing their name:

  * **One question per episode, answered inside it.**  Jesse Armstrong's fourth
    season of Succession fixes the form -- "Today, can X do Y?" -- and answers
    it before the hour ends.  An episode with no such question has no reason to
    stop where it stops.

  * **No shot without a turn.**  McKee: mark the value at the open and again at
    the close; if they are the same, the scene exists to explain something, and
    explanation belongs inside another scene's picture.  This is the story-side
    statement of the fault we kept meeting as a RENDER fault: a shot whose value
    does not turn is a shot with nothing to photograph, and it comes back
    frozen.  The freeze was never the engine's idea.

Both are REPORTED, never refused.  Episode 1 was cut before either field
existed, and a story lint that raises would block a finished episode over a
rule its plan predates.
"""
from __future__ import annotations

import re

ARROW = "->"
"""How a turn is written: the value before, the value after."""

QUESTION = re.compile(r"^\s*today,\s*can\s+\S+.*\?\s*$", re.IGNORECASE)
"""Armstrong's form.  "Today" is what makes it answerable in one episode, and
"can" is what makes the answer yes or no rather than an essay."""


def question_shape(question: str) -> bool:
    """Is the episode's question in the form that can be answered by an ending?"""
    return bool(QUESTION.match(question or ""))


def sides(turn: str) -> tuple[str, str]:
    """The value before and after, lowercased and stripped."""
    before, _, after = (turn or "").partition(ARROW)
    return before.strip().lower(), after.strip().lower()


def turns(turn: str) -> bool:
    """A turn needs two DIFFERENT values, written either side of the arrow."""
    before, after = sides(turn)
    return bool(before and after and before != after)


def turnless(shots) -> list[int]:
    """The shots that declare no turn, or declare the same value on both sides."""
    return [shot.index for shot in shots if not turns(getattr(shot, "turn", ""))]


def report(spec_question: str, shots) -> dict:
    """The story verdict: what is missing, said in one line, and never raised."""
    empty = turnless(shots)
    ok = question_shape(spec_question)
    says = []
    if not ok:
        says.append('no episode question in the form "Today, can X do Y?"'
                    if not spec_question else f"the question does not answer in one episode: {spec_question!r}")
    if empty:
        says.append(f"{len(empty)} shots turn no value: {empty}")
    return {"question_ok": ok, "turnless": empty, "passed": ok and not empty,
            "says": "; ".join(says) or "every shot turns a value and the episode asks one question"}
