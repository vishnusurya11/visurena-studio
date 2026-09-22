"""What is actually IN a picture, read by the local vision model and judged here.

Every other gate in this pipeline measures a statistic -- edge strength, face
count, frozen share, mux lag. None of them looks at the frame. So a doll in a
pink dress, a horse cropped to its head, three men drawn as one man three
times, hills on a flat Surrey horizon and a Sherlock Holmes title card on a
War of the Worlds episode all passed DQ, and were caught by eye or by the
owner (2026-09-21: "you have to do a lot of dq on these prompts and videos").

THE MODEL IS NEVER ASKED WHETHER THE PICTURE IS RIGHT. A VLM says yes. It is
asked to LIST what it sees in a closed vocabulary and the judging is done in
this file, against the shot's own words -- the rule `studio/describe.py`
established for trait cards, applied to content.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

LANDFORMS = ("flat", "gentle rise", "hills", "mountains", "cliffs", "indoors")
"""What the ground may read as. The book's own country decides which of these
is a fault: Horsell, Woking and Maybury are flat heath and river terrace, and
ep05's T06 and ep07's shot 0 both grew hills the prompt never asked for."""

RAISED = ("hills", "mountains", "cliffs")

HOURS = ("day", "dusk", "night")


@dataclass(frozen=True)
class Seen:
    """One picture as the reader saw it, in the closed vocabulary."""
    landform: str = "flat"
    people: int = 0
    lookalikes: int = 0
    text: bool = False
    hour: str = "night"
    subjects: list[str] = field(default_factory=list)


ASK = (
    "Describe this picture by ANSWERING EACH QUESTION with one of the allowed "
    "answers and nothing else. Output strict JSON with these keys.\n"
    '"landform": the shape of the ground, one of ' + ", ".join(LANDFORMS) + ".\n"
    '"people": how many human figures you can see, as a number.\n'
    '"lookalikes": how many of those figures look like copies of another one '
    "(same face, same build, same clothes), as a number.\n"
    '"text": true if any letters, words, numbers or captions appear anywhere, '
    "else false.\n"
    '"hour": the time of day the LIGHT says, one of ' + ", ".join(HOURS) + ".\n"
    '"subjects": a list of the things in the picture, each a short plain noun '
    "phrase, everything you can name, including anything unexpected."
)


def forbidden_landform(seen: Seen, flat: bool) -> bool:
    """Ground that rises where the book's country does not."""
    return flat and seen.landform in RAISED


def reads_as_night(seen: Seen) -> bool:
    return seen.hour != "day"


WORD = re.compile(r"[a-z]+")


def unasked_subject(seen: Seen, frame: str) -> list[str]:
    """Subjects the reader saw that the shot's own words never mention.

    A subject counts as asked for when ANY of its words is in the shot's
    prose: "pine trees" answers "bare pine trunks", and "a child's doll"
    answers nothing at all.
    """
    said = {stem(w) for w in WORD.findall((frame or "").lower())}
    out = []
    for subject in seen.subjects:
        words = [stem(w) for w in WORD.findall(subject.lower()) if len(w) > 2]
        if words and not (set(words) & said):
            out.append(subject)
    return out


def stem(word: str) -> str:
    """Enough of a word to match its plural: the reader says "pine trees" where
    the shot says "bare pine trunks ... among the pines", and those agree."""
    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"
    # ONLY the plural s. Stripping "es" turned "pines" into "pin" and "trees"
    # into "tre", so a picture of pine trees read as unasked-for in a shot
    # about pines.
    if word.endswith("s") and len(word) > 3:
        return word[:-1]
    return word


def people_fault(seen: Seen, planned: int, crowd: bool) -> bool:
    """More faces than the shot casts, or a crowd made of one repeated person."""
    if seen.lookalikes:
        return True
    return not crowd and seen.people > planned


def faults(seen: Seen, frame: str, planned: int, crowd: bool,
           flat: bool, night: bool) -> list[str]:
    """Every way this picture disagrees with the shot that asked for it."""
    out = []
    if forbidden_landform(seen, flat):
        out.append(f"landform {seen.landform!r}: this country is flat")
    if strangers := unasked_subject(seen, frame):
        out.append(f"the shot never asked for {', '.join(strangers)}")
    if people_fault(seen, planned, crowd):
        out.append(f"{seen.people} figure(s) for {planned} cast, "
                   f"{seen.lookalikes} of them copies of another")
    if seen.text:
        out.append("text or lettering in the picture")
    if night and not reads_as_night(seen):
        out.append(f"the hour reads {seen.hour!r} and the shot is at night")
    return out
