"""Writing the prompt for one shot.

Three things go in, and each is there because leaving it out has a known cost:

*   The character's physical description, VERBATIM and identically every time.
    References pin the instance; the words pin the category, and the measured
    finding is that both are needed -- a shared seed alone produced a
    completely different person wearing different clothes.
*   An explicit camera clause.  H3 drifts by default when the prompt says
    nothing about the camera, and its vocabulary is a closed set written as
    prose with amplitude and speed, not bracket tags.  `[Push in]` is the
    HOSTED Hailuo dialect and does nothing here.
*   The negatives, inside the positive prompt.  H3's guider has no negative
    input at all -- there is literally nowhere else to put them.
"""
from __future__ import annotations

NO_TYPE = ("All frames free of text: no signage, no lettering, no subtitles, "
           "no watermarks, no captions, no on-screen writing.")

CAMERA: dict[str, tuple[str, ...]] = {
    "quiet": (
        "The camera pushes in with small amplitude at slow speed.",
        "The camera is a static shot, the frame perfectly still.",
        "The camera tilts down with small amplitude at slow speed.",
    ),
    "build": (
        "The camera tracks left with small amplitude at slow speed.",
        "The camera arcs around the subject at slow speed.",
        "The camera pushes in with large amplitude at slow speed.",
    ),
    "hit": (
        "The camera pushes in with large amplitude at fast speed.",
        "The camera shakes slightly, handheld, at fast speed.",
        "The camera pulls out with large amplitude at fast speed.",
    ),
    "aftermath": (
        "The camera is a static shot, the frame perfectly still.",
        "The camera pulls out with small amplitude at slow speed.",
    ),
}
"""H3's documented motion vocabulary, several per register.

Written as prose with amplitude and speed, which the guide requires -- stacked
labels at the end of a sentence are off-spec, and `[Push in]` bracket syntax
is the HOSTED Hailuo dialect that does nothing here.

Several per register rather than one because uniform treatment across every
shot is itself the pattern an audience detects, and a slow drifting push is
the single most recognisable tell of generated video.  H3 also drifts by
default when the prompt says nothing about the camera, so a static frame must
be asked for explicitly.
"""


def camera_for(arc: str, index: int) -> str:
    """A camera move for this beat: right register, varied within it."""
    moves = CAMERA.get(arc) or CAMERA["build"]
    return moves[index % len(moves)]


FRAMING: dict[str, str] = {
    "quiet": "A medium shot, the figure from the waist up, filling much of the frame.",
    "build": "A medium close shot, the face clearly visible and well lit.",
    "hit": "A close shot, the head and shoulders filling the frame.",
    "aftermath": "A medium close shot, the face clearly visible.",
}
"""How big the person sits in frame.

Faces collapse on wide shots at any resolution, and the driver is HEAD SIZE
IN FRAME rather than pixel count -- so this is not something more resolution
fixes.  Saying nothing about framing let the model compose establishing wides
around the location plate: the first two clips read unmistakably as the
Criterion and as 221B, and in neither could you see who the person was.

A trailer in the literary register sells faces and a world.  It can afford
two or three establishing wides -- more than that is itself a named amateur
tell -- so the wides already rendered are kept and everything after them
comes in closer.
"""


def framing_for(arc: str) -> str:
    return FRAMING.get(arc, FRAMING["build"])


def picture_roll(count: int) -> str:
    """Name the reference slots so the prompt can address them.

    `<Picture i>` binds POSITIONALLY to reference slot i, so the order these
    are written must match the order the refs are injected.
    """
    return " ".join(f"<Picture {i + 1}>" for i in range(count))


def shot_prompt(style: str, physical: list[str], place: str, action: str,
                arc: str, seconds: float, index: int = 0) -> str:
    """One H3 shot prompt: subject, place, action, camera, then the negatives."""
    described = [d for d in physical if d and d.strip()]
    if described:
        subject = f"The person in <Picture 1> is {' '.join(described)}"
    elif physical:
        # The book never says what they look like.  The reference image is
        # then the ONLY statement of identity, and inventing prose here would
        # contradict it rather than reinforce it.
        subject = "The person shown in <Picture 1> appears in this scene."
    else:
        subject = "No people are visible."
    return (
        f"{style} {subject} "
        f"The location is {place}. "
        f"{framing_for(arc) if physical else ''} "
        f"{action} {camera_for(arc, index)} "
        f"The shot runs {seconds:.1f} seconds as one continuous take with no cuts. "
        f"{NO_TYPE}"
    )


SHEET_WORDS = ("character reference", "mid-grey backdrop", "studio light",
               "facing camera", "full figure", "no cast shadows", "turnaround")
"""Language that belongs on a reference SHEET and must never reach a shot.

A reference sheet prompt and a shot prompt describe opposite things: one wants
a person centred on grey with flat light, the other wants them inside a scene.
Feeding the sheet prompt to the video model asks it to animate a character
sheet.  That happened -- a fragile `split("sharp focus.")` silently failed to
match and passed the entire sheet prompt through as the character description.
"""


def is_scene_safe(description: str) -> bool:
    """True when a description says who someone is, not how to photograph them."""
    lowered = description.lower()
    return not any(word in lowered for word in SHEET_WORDS)
