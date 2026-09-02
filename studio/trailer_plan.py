"""Choosing what goes in the trailer, mechanically, from the screenplay.

No model is asked which moments matter.  The screenplay already records what
the trailer needs -- who is present, where, what is said, with what emotion --
so selection is arithmetic over that record, and arithmetic is reproducible,
free, and auditable.  A judgement call that cannot be re-derived tomorrow is
not a decision, it is a mood.

The shape is Derek Lieu's four-part trailer: cold open, introduction,
escalation, climax.  Its load-bearing rule is the one auto-cut trailers break
-- energy must FALL between sections, because a braam every four seconds is
not a trailer, it is noise.
"""
from __future__ import annotations

from studio.trailer_spec import Register, TrailerBeat

MAX_LINE_WORDS = 14
"""A trailer line is read in one breath over one shot.  Longer is a scene."""


def is_quotable(element: dict) -> bool:
    """A dialogue line short and self-contained enough to stand alone."""
    if element.get("kind") != "dialogue" or not element.get("character"):
        return False
    text = (element.get("text") or "").strip()
    if not text or len(text.split()) > MAX_LINE_WORDS:
        return False
    return not text.endswith(("...", "--", "—"))


def quotable_lines(scene: dict) -> list[dict]:
    """Every line in a scene that could carry a trailer shot on its own."""
    return [e for e in scene.get("elements", []) if is_quotable(e)]


def arc_for(position: float) -> Register:
    """Where a beat sits in the trailer's rise, from its fractional position.

    The aftermath tail is deliberate: something must come after the climax or
    the hard-out has nothing to land against.
    """
    if position < 0.25:
        return "quiet"
    if position < 0.70:
        return "build"
    if position < 0.92:
        return "hit"
    return "aftermath"


def scene_value(scene: dict, protagonist: str | None) -> int:
    """How much trailer a scene is worth.  Deliberately crude and readable."""
    value = 0
    if protagonist and protagonist in scene.get("cast", []):
        value += 3
    value += min(len(quotable_lines(scene)), 3)
    value += min(len(scene.get("cast", [])), 2)
    if scene.get("slug", {}).get("int_ext") == "EXT":
        value += 1
    return value


def spread_across(scenes: list[dict], count: int) -> list[dict]:
    """Take `count` scenes spanning the whole story, not the best clustered.

    A trailer that draws its beats from one act shows one act.  Sampling by
    position first, then choosing the strongest inside each window, keeps the
    story's shape while still preferring good scenes.
    """
    if count >= len(scenes):
        return list(scenes)
    windows: list[list[dict]] = [[] for _ in range(count)]
    for index, scene in enumerate(scenes):
        windows[min(index * count // len(scenes), count - 1)].append(scene)
    return [w[0] for w in windows if w]


def best_in_window(window: list[dict], protagonist: str | None) -> dict:
    """The scene in a window worth the most, ties broken by earliest."""
    return max(window, key=lambda s: (scene_value(s, protagonist), -s["number"]))


def pick_scenes(scenes: list[dict], count: int, protagonist: str | None) -> list[dict]:
    """`count` scenes, spread across the story, strongest within each window."""
    if count >= len(scenes):
        return list(scenes)
    windows: list[list[dict]] = [[] for _ in range(count)]
    for index, scene in enumerate(scenes):
        windows[min(index * count // len(scenes), count - 1)].append(scene)
    return [best_in_window(w, protagonist) for w in windows if w]


def unique_locations(scenes: list[dict]) -> list[str]:
    """Location ids in first-appearance order -- what needs a ref plate."""
    seen: list[str] = []
    for scene in scenes:
        loc = scene.get("slug", {}).get("location_id")
        if loc and loc not in seen:
            seen.append(loc)
    return seen


def speaking_characters(scenes: list[dict]) -> list[str]:
    """Characters who actually say something, in first-appearance order.

    Cast is who is present; this is who the audience will attach a voice and
    therefore a face to.  Reference sheets are expensive; spend them here.
    """
    seen: list[str] = []
    for scene in scenes:
        for line in quotable_lines(scene):
            who = line["character"]
            if who not in seen:
                seen.append(who)
    return seen
