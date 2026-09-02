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

CAMERA = {
    "quiet": "The camera pushes in with small amplitude at slow speed.",
    "build": "The camera tracks with small amplitude at slow speed.",
    "hit": "The camera pushes in with large amplitude at fast speed.",
    "aftermath": "The camera is static, holding the frame.",
}
"""H3's documented motion vocabulary, one per position in the arc.  Written as
natural English inside the shot, which the guide requires -- stacked labels at
the end of a sentence are off-spec."""


def picture_roll(count: int) -> str:
    """Name the reference slots so the prompt can address them.

    `<Picture i>` binds POSITIONALLY to reference slot i, so the order these
    are written must match the order the refs are injected.
    """
    return " ".join(f"<Picture {i + 1}>" for i in range(count))


def shot_prompt(style: str, physical: list[str], place: str, action: str,
                arc: str, seconds: float) -> str:
    """One H3 shot prompt: subject, place, action, camera, then the negatives."""
    people = " ".join(physical)
    subject = (f"The person in <Picture 1> is {people}" if physical
               else "No people are visible.")
    return (
        f"{style} {subject} "
        f"The location is {place}. "
        f"{action} {CAMERA.get(arc, CAMERA['build'])} "
        f"The shot runs {seconds:.1f} seconds as one continuous take with no cuts. "
        f"{NO_TYPE}"
    )
