"""Writing a MiniMax-H3 reference-to-video prompt to its actual specification.

We were sending one flat ~120-word paragraph.  H3's published Ref2VA guide asks
for a six-section document, and one of those sections exists precisely to say
what identity binding needs and had no home in our text:

    subject_definitions   what each reference IS
    summary               one paragraph, task-type prefix in brackets
    retention_analysis    HOW each reference is preserved -- one line per label
    detailed_description  350-500 words, shot by shot, labels inserted
    overall_soundscape    ambience and physical sound
    non_diegetic_music    score the characters cannot hear

`retention_analysis` is the field for "keep this face, change everything else".
Its markers are a closed set: fully_preserved, partially_preserved,
attribute_transfer, weak_reference.  We had been asserting that relationship
implicitly and hoping.

Two label types, and they are not interchangeable: <Subject N> is reusable
visible content -- a person, a style -- and <Picture N> is a concrete frame
anchor.  Both bind POSITIONALLY to the reference slot of the same number, so
reordering the injected images silently repoints every tag in the text.
"""
from __future__ import annotations

RETENTION = ("fully_preserved", "partially_preserved", "attribute_transfer",
             "weak_reference")


def subject_definitions(character: str | None, place: str, second: str = "") -> str:
    """Declare what each reference is, before anything refers to it.

    Two people fill both slots and the place goes by prompt: H3 takes two
    references, and a two-shot needs both faces more than it needs the room.
    """
    lines = []
    if character and second:
        lines.append(f"<Subject 1>: The person whose identity, face, build and "
                     f"dress the target video must keep. {character}")
        lines.append(f"<Subject 2>: The second person, a different individual, "
                     f"whose identity, face, build and dress the target video "
                     f"must also keep. {second}")
    elif character:
        lines.append(f"<Subject 1>: The person whose identity, face, build and "
                     f"dress the target video must keep. {character}")
        lines.append(f"<Subject 2>: {place} The location whose architecture, "
                     f"materials and light the target video is set in.")
    else:
        lines.append(f"<Subject 1>: {place} The location whose architecture, "
                     f"materials and light the target video is set in.")
    return "\n".join(lines)


def retention_analysis(has_character: bool, has_second: bool = False) -> str:
    """State how each reference survives into the shot.

    The character is fully_preserved -- that IS the binding.  The location is
    only attribute_transfer, which is an honest description of what was
    measured: a bar-interior plate plus a slug name produced an arcade carrying
    the bar's tables and gaslights.  Claiming fully_preserved for a place the
    model blends anyway would be asserting something the output contradicts.
    """
    if has_character and has_second:
        return ("<Subject 1>: fully_preserved. The face, build, hair and "
                "clothing are carried into the new scene unchanged.\n"
                "<Subject 2>: fully_preserved. The face, build, hair and "
                "clothing are carried into the new scene unchanged; the two "
                "people are never merged into one.")
    if has_character:
        return ("<Subject 1>: fully_preserved. The face, build, hair and "
                "clothing are carried into the new scene unchanged; only the "
                "lighting, framing and action differ.\n"
                "<Subject 2>: attribute_transfer. The palette, materials, "
                "period and quality of light are carried over; the exact "
                "architecture may differ.")
    return ("<Subject 1>: attribute_transfer. The palette, materials, period "
            "and quality of light are carried over; the exact architecture "
            "may differ.")


SECTIONS = ("subject_definitions", "summary", "retention_analysis",
            "detailed_description", "overall_soundscape", "non_diegetic_music")
"""The order H3's own guide specifies.  Order is part of the format."""

TARGET_WORDS = (350, 500)


def word_count(text: str) -> int:
    return len(text.split())


def summary(action: str, place: str, seconds: float, has_second: bool = False) -> str:
    """One paragraph, prefixed with the task type in brackets."""
    kept = ("The identities of the people in <Subject 1> and <Subject 2> are"
            if has_second else "The identity of the person in <Subject 1> is")
    return (f"[Reference to Video] A single continuous {seconds:.0f}-second take. "
            f"{action.rstrip('.')}, in {place}. {kept} preserved exactly; the "
            f"camera moves once, and the take does not cut.")


def detailed_description(character: str, place: str, action: str,
                         open_framing: str, close_framing: str, camera: str,
                         seconds: float, style: str, second: str = "") -> str:
    """The 350-500 word body, opening wide and ending tight.

    Written as one traversal rather than a list of shots, because the clip is a
    long take that the edit cuts several sizes out of -- so the take has to
    CONTAIN those sizes, in the order the cut will want them.  Opening on the
    wider framing and arriving at the tighter one is what makes both available
    to the editor from one render.
    """
    who = (f"The person in <Subject 1>: {character} " if character
           else "No people are visible in this shot. ")
    if character and second:
        who += (f"The person in <Subject 2>: {second} They are two different "
                f"people, each keeping their own face throughout. ")
    body = [
        f"{style}",
        f"The setting is {place}, established in the first moments of the take "
        f"and held throughout; the geometry of the room does not change.",
        who,
        f"The take opens on this framing. {open_framing}",
        f"The action of the shot is as follows. {action}",
        f"{camera}",
        f"As the move completes, the frame arrives at this composition. "
        f"{close_framing}",
        f"The light is motivated by a single dominant source within the scene, "
        f"falling across the subject from one side so that the shadowed side of "
        f"the face retains detail rather than going to black. Dust and haze in "
        f"the air catch that light and make its direction visible. Surfaces "
        f"read as physical materials with weight and age: cloth with a nap, wood "
        f"with a grain, metal with tarnish, glass with reflections that move as "
        f"the camera moves.",
        f"Parallax is visible throughout the move: objects nearest the lens "
        f"travel across the frame faster than the background behind them, and "
        f"the relationship between foreground and background changes as the "
        f"camera travels. This is what makes the movement read as a camera in a "
        f"real space rather than a still image being scaled.",
        f"The performance is contained and specific rather than broad. Small "
        f"movements of the head, the eyes and the hands carry the moment; there "
        f"is no exaggerated gesture and no acting toward the lens. The subject "
        f"does not look into the camera at any point.",
        f"Motion is continuous and physically plausible from the first frame to "
        f"the last. Nothing in the frame teleports, duplicates, or changes "
        f"identity partway through. Hands keep five fingers, objects keep their "
        f"shape, and anything the subject is holding stays in their grip.",
        f"The entire {seconds:.1f} seconds is one continuous take with no cuts, "
        f"no dissolves, no speed changes and no camera stops.",
    ]
    return " ".join(part.strip() for part in body if part.strip())


def soundscape(place: str) -> str:
    """Ambience and physical sound: what the microphone in the room hears."""
    return (f"The ambience of {place}, recorded close and dry: the room tone of "
            f"the space itself, the small physical sounds the action makes -- "
            f"cloth, footfall, breath, the contact of objects with surfaces. No "
            f"speech, no crowd, no music within the scene.")


def music(arc: str) -> str:
    """Score the characters cannot hear.  A trailer supplies its own; this
    section exists to tell H3 NOT to invent one that fights it."""
    return ("No non-diegetic music. The take is scored externally and any music "
            "generated here would fight the trailer's own cue.")


def build(style: str, character: str, place: str, action: str,
          open_framing: str, close_framing: str, camera: str,
          seconds: float, arc: str = "build", second: str = "") -> str:
    """The whole six-section document, in the order the spec names."""
    two = bool(character and second)
    parts = {
        "subject_definitions": subject_definitions(character or None, place, second),
        "summary": summary(action, place, seconds, two),
        "retention_analysis": retention_analysis(bool(character), two),
        "detailed_description": detailed_description(
            character, place, action, open_framing, close_framing, camera,
            seconds, style, second),
        "overall_soundscape": soundscape(place),
        "non_diegetic_music": music(arc),
    }
    return "\n\n".join(f"{name}:\n{parts[name]}" for name in SECTIONS)
