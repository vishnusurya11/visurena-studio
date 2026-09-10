"""The Ref2V document for one beat, written so the SUBJECT dominates it.

WHY THIS EXISTS.  `h3_prompt.build` produced the documents the first
script-driven render used, and its pictures were wrong in a way that is
measurable rather than a matter of taste:

  * B08's prompt ran 1009 words and said "pills" TWICE.
  * 303 of those words were byte-identical across all eighteen prompts --
    generic light, parallax, materials, performance, continuity.
  * ~150 more re-described Holmes' face in prose, while the reference IMAGE
    was already carrying his face.
  * B05 contradicted itself: "the shot holds an EMPTY 3 Lauriston Gardens"
    followed by "a gloved hand lifting a pill", and "the shadowed side of the
    FACE keeps visible detail" in a shot with no face.

Handed that, the model rendered what the document actually emphasised -- the
boilerplate -- and invented plausible objects for the table.  It drew candles.

So this document states the subject FIRST, repeats it at the close, keeps the
generic craft language to one line each, and never asserts something the shot
contradicts.  The identity still binds by LABEL (`<Subject 1>`,
`fully_preserved`), which is what actually holds a face, rather than by prose.
"""
from __future__ import annotations

SECTIONS = ("subject_definitions", "summary", "retention_analysis",
            "detailed_description", "overall_soundscape", "non_diegetic_music")

EMPTY_WORDS = ("hand", "figure", "man", "woman", "he ", "she ", "they ",
               "holmes", "watson", "someone", "arm", "fingers")
"""Words whose presence in the action means somebody is in frame, whatever the
reference slots say.  A shot may bind no face and still show a gloved hand."""


def peopled(character: str, action: str, subject: str) -> bool:
    """Whether a person is in frame at all -- bound or merely described."""
    if character:
        return True
    text = f"{action} {subject}".lower()
    return any(word in text for word in EMPTY_WORDS)


def subject_definitions(character: str, place: str, second: str = "") -> str:
    """What each reference IS, before anything refers to it."""
    if character and second:
        return (f"<Subject 1>: The person whose identity, face, build and dress the "
                f"video must keep. {character}\n"
                f"<Subject 2>: A second, different person, whose identity, face, "
                f"build and dress the video must also keep. {second}")
    if character:
        return (f"<Subject 1>: The person whose identity, face, build and dress the "
                f"video must keep. {character}\n"
                f"<Subject 2>: {place} The location whose architecture, materials "
                f"and light the video is set in.")
    return (f"<Subject 1>: {place} The location whose architecture, materials and "
            f"light the video is set in.")


def retention_analysis(character: str, second: str = "") -> str:
    """How each reference survives into the shot."""
    if character and second:
        return ("<Subject 1>: fully_preserved -- the face and dress are kept exactly.\n"
                "<Subject 2>: fully_preserved -- a different face, kept exactly.")
    if character:
        return ("<Subject 1>: fully_preserved -- the face and dress are kept exactly.\n"
                "<Subject 2>: attribute_transfer -- the place lends its materials and light.")
    return "<Subject 1>: attribute_transfer -- the place lends its materials and light."


def summary(subject: str, place: str, seconds: float, character: str) -> str:
    """One paragraph, task type in brackets, the SUBJECT in the first clause."""
    kept = (" The identity of the person in <Subject 1> is preserved exactly."
            if character else "")
    return (f"[Reference to Video] {subject.rstrip('.')} -- a single continuous "
            f"{seconds:.0f}-second take in {place}.{kept} The camera moves once, "
            f"and the take runs unbroken from the first frame to the last.")


def lighting(character: str, peopled_shot: bool) -> str:
    """One line, and it lights what is actually in frame."""
    if character:
        return ("The light comes from one dominant source inside the scene, across the "
                "subject from one side, so the shadowed side of the face keeps detail.")
    if peopled_shot:
        return ("The light comes from one dominant source inside the scene, raking "
                "across the hands and the objects they touch.")
    return ("The light comes from one dominant source inside the scene, raking across "
            "the surfaces and picking out their texture.")


def occupancy(character: str, peopled_shot: bool, place: str) -> str:
    """Who is in the frame -- and only claims emptiness when it is empty."""
    if character:
        return "The person in <Subject 1> holds the frame throughout."
    if peopled_shot:
        return "Only hands and the objects they touch are seen; no face enters frame."
    return (f"Nothing enters the frame but the place itself: {place} is its own "
            f"only occupant, and the movement is the air and the light.")


def detailed_description(subject: str, action: str, open_framing: str,
                         close_framing: str, camera: str, seconds: float,
                         style: str, place: str, character: str) -> str:
    """The body, with the subject first and last and the craft language thin."""
    here = peopled(character, action, subject)
    return " ".join([
        f"{subject.rstrip('.')}.",
        f"{style}",
        f"The setting is {place}, held throughout in one fixed geometry.",
        occupancy(character, here, place),
        f"The take opens on this framing. {open_framing}",
        f"The action: {action}",
        f"{camera}",
        f"It arrives here. {close_framing}",
        lighting(character, here),
        "Surfaces read as physical materials with weight and age, and the "
        "foreground moves faster than the background as the camera travels.",
        "Every object and every person keeps one continuous position, one body "
        "and one identity from the first frame to the last.",
        f"The whole {seconds:.1f} seconds is one unbroken take at one constant "
        f"speed, and it ends on {subject.rstrip('.')}.",
    ])


def soundscape(place: str) -> str:
    return (f"The ambience of {place}, recorded close and dry: room tone and the "
            f"small sounds the action makes -- cloth, footfall, breath, the contact "
            f"of objects with surfaces.")


def music() -> str:
    return ("This take carries its diegetic sound alone; the trailer's own cue is "
            "laid over it later in the edit.")


def build(style: str, character: str, place: str, subject: str, action: str,
          open_framing: str, close_framing: str, camera: str, seconds: float,
          second: str = "") -> str:
    """The six-section document, in the order the spec names."""
    parts = {
        "subject_definitions": subject_definitions(character, place, second),
        "summary": summary(subject, place, seconds, character),
        "retention_analysis": retention_analysis(character, second),
        "detailed_description": detailed_description(
            subject, action, open_framing, close_framing, camera, seconds,
            style, place, character),
        "overall_soundscape": soundscape(place),
        "non_diegetic_music": music(),
    }
    return "\n\n".join(f"{name}:\n{parts[name]}" for name in SECTIONS)
