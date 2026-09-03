"""Deriving a trailer's dramatic structure from a screenplay.

The previous selector spread eleven scenes evenly across the story and cycled
each three times.  That is a sampler, not a trailer: it had no protagonist
logic, no turn, and it answered its own logline halfway through.

Everything here is derived from screenplay.json alone -- no model, no spend --
and every function is a pure function of that data so it can be tested against
fixtures.
"""
from __future__ import annotations

import re

CONNECTIVES = (" until ", " whose ", " before ", " only to ", " and discovers ",
               " to reveal ", " while ", " when he ", " when she ")
"""A logline's hinge.  Everything AFTER it is the thing the trailer sells by
withholding, so it marks the forbidden zone."""

STOPWORDS = {"the", "a", "an", "of", "and", "or", "to", "in", "on", "at", "by",
             "for", "with", "his", "her", "their", "its", "that", "this", "is",
             "are", "was", "were", "be", "been", "from", "as", "it", "he", "she"}


def people_in(scene: dict) -> set[str]:
    """Everyone present or speaking in a scene."""
    return set(scene.get("cast") or []) | set(scene.get("speaking") or [])


def lead_of(scenes: list[dict]) -> str | None:
    """The character present in the most scenes -- the story's centre."""
    counts: dict[str, int] = {}
    for scene in scenes:
        for who in people_in(scene):
            counts[who] = counts.get(who, 0) + 1
    return max(counts, key=lambda w: (counts[w], w)) if counts else None


def figure_of(scenes: list[dict], lead: str | None) -> str | None:
    """The opposition: whoever owns the most story mass OUTSIDE the lead's view.

    Not "the second most present character" -- that is usually a companion.
    The antagonist is the one the protagonist keeps missing.
    """
    shadow: dict[str, int] = {}
    for scene in scenes:
        present = people_in(scene)
        if lead in present:
            continue
        for who in present:
            if who != lead:
                shadow[who] = shadow.get(who, 0) + 1
    return max(shadow, key=lambda w: (shadow[w], w)) if shadow else None


def turn_of(scenes: list[dict], lead: str | None) -> dict | None:
    """The first scene of the longest run in which the lead is absent.

    For an adaptation the turn is not a plot reveal -- it is the moment the
    narration changes hands.  Run on these two books it lands on Part II of
    A Study in Scarlet and on Henry Jekyll's Full Statement, which are exactly
    where each book breaks.
    """
    best_len = best_start = current = 0
    start = 0
    for index, scene in enumerate(scenes):
        if lead in people_in(scene):
            current = 0
            continue
        if current == 0:
            start = index
        current += 1
        if current > best_len:
            best_len, best_start = current, start
    return scenes[best_start] if best_len else None


def forbidden_words(logline: str, scenes: list[dict],
                    max_share: float = 0.30) -> set[str]:
    """Content words from the logline's final clause that actually discriminate.

    A logline reads "When <A>, <B> until <C>".  <A> and <B> are the promise;
    <C> is the payoff, and a trailer that shows <C> has answered its own
    question.  Both shipped trailers did exactly that, in both cases with the
    forbidden material arriving as a spoken line.

    Rarity matters as much as membership.  Taking the tail's words verbatim put
    "jekyll" in the forbidden set, which appears in 39 of 50 scenes and would
    ban the book -- so a word present in more than `max_share` of scenes is
    dropped as too common to mean anything.
    """
    lowered = logline.lower()
    tail = ""
    for connective in CONNECTIVES:
        if connective in lowered:
            tail = lowered.split(connective, 1)[1]
            break
    if not tail:
        return set()
    candidates = {w for w in re.findall(r"[a-z']{4,}", tail) if w not in STOPWORDS}
    texts = [" ".join(e.get("text", "") for e in sc.get("elements", [])).lower()
             for sc in scenes]
    limit = max_share * max(len(texts), 1)
    return {w for w in candidates if sum(w in t for t in texts) <= limit}


def scene_is_forbidden(scene: dict, forbidden: set[str], threshold: int = 2) -> bool:
    """True when a scene depicts the logline's withheld payoff."""
    if not forbidden:
        return False
    text = " ".join(e.get("text", "") for e in scene.get("elements", [])).lower()
    return sum(1 for word in forbidden if word in text) >= threshold


def action_elements(scenes: list[dict], min_words: int = 4) -> list[dict]:
    """Every action line in the book, as an individual shot candidate.

    THIS is the fix for repetition.  The scene is not the trailer's atom -- a
    scene is ninety seconds of story and a trailer shot is two.  Selecting
    scenes gave 11 candidates for 33 shots, so every setup repeated three
    times; selecting ELEMENTS gives 268 candidates for the same 33 shots.
    """
    found: list[dict] = []
    for scene in scenes:
        for index, element in enumerate(scene.get("elements", [])):
            if element.get("kind") != "action":
                continue
            text = (element.get("text") or "").strip()
            if len(text.split()) < min_words:
                continue
            found.append({"scene": scene["number"], "index": index, "text": text,
                          "location_id": scene.get("slug", {}).get("location_id"),
                          "int_ext": scene.get("slug", {}).get("int_ext"),
                          "time": scene.get("slug", {}).get("time"),
                          "cast": list(people_in(scene))})
    return found


def resolution_scenes(scenes: list[dict], lead: str | None, figure: str | None,
                      tail_share: float = 0.15) -> set[int]:
    """Scene numbers that give the story away, by STRUCTURE not by vocabulary.

    Matching the logline's words against scene text does not work: a logline is
    abstract ("whose solution exposes a decades-old revenge") and action lines
    are concrete ("Hope releases the bridle"), so the words never meet.  Two
    structural facts identify the payoff instead, and both are exact:

    * the story's last stretch IS the resolution, in any book;
    * the scene where the lead and the opposition finally stand in the same
      room is the answer to the question the whole trailer is asking.

    These may still be SHOWN -- an image gives nothing away on its own -- but
    only briefly and never carrying a line.  You may show it; you may not
    caption it.
    """
    if not scenes:
        return set()
    cutoff = len(scenes) - max(1, int(len(scenes) * tail_share))
    banned = {sc["number"] for sc in scenes[cutoff:]}
    if lead and figure:
        # The LAST time they stand together, not every time.  In Jekyll and
        # Hyde the two meet early and often -- that is the premise, not the
        # payoff -- and banning every meeting would ban the first third.
        meetings = [sc["number"] for sc in scenes if {lead, figure} <= people_in(sc)]
        if meetings:
            banned.add(meetings[-1])
    return banned


CONCRETE = ("door", "hand", "face", "window", "light", "candle", "lamp", "knife",
            "blood", "letter", "paper", "key", "glass", "fire", "street", "stair",
            "mirror", "coat", "cab", "horse", "gun", "pistol", "body", "eyes",
            "watch", "ring", "box", "bottle", "table", "floor", "wall", "smoke")
ABSTRACT = ("realis", "understand", "consider", "remember", "decide", "wonder",
            "seem", "appear to", "later", "meanwhile", "we learn", "it becomes")


def element_value(element: dict, lead: str | None, figure: str | None) -> float:
    """How much trailer one action line is worth.

    Concreteness dominates.  A shot is a photograph, so a line naming a thing a
    camera can point at is worth more than one describing a state of mind --
    "A great blue anchor marks the back of the man's hand" is a shot;
    "Holmes considers the problem" is not.
    """
    text = element["text"].lower()
    score = 0.0
    score += 2.0 * sum(word in text for word in CONCRETE)
    score -= 3.0 * sum(word in text for word in ABSTRACT)
    if lead and lead in element["cast"]:
        score += 1.5
    if figure and figure in element["cast"]:
        score += 1.2
    words = len(text.split())
    score += 1.5 if 6 <= words <= 22 else -1.0
    if element.get("int_ext") == "EXT":
        score += 0.5
    return score


def select_setups(scenes: list[dict], count: int, lead: str | None,
                  figure: str | None, restricted: set[int]) -> list[dict]:
    """`count` distinct visual setups, spread across the story's shape.

    One element per setup, at most one per scene, and no location used more
    than twice -- the previous selector's whole failure was that eleven scenes
    had to carry thirty-three shots, so each appeared three times over.
    """
    candidates = [e for e in action_elements(scenes) if e["scene"] not in restricted]
    if not candidates:
        return []
    windows: list[list[dict]] = [[] for _ in range(count)]
    span = max(sc["number"] for sc in scenes)
    for element in candidates:
        index = min(int((element["scene"] - 1) / span * count), count - 1)
        windows[index].append(element)

    chosen: list[dict] = []
    used_scenes: set[int] = set()
    used_places: dict[str, int] = {}
    for window in windows:
        ranked = sorted(window, key=lambda e: -element_value(e, lead, figure))
        for element in ranked:
            place = element["location_id"]
            if element["scene"] in used_scenes or used_places.get(place, 0) >= 2:
                continue
            chosen.append(element)
            used_scenes.add(element["scene"])
            used_places[place] = used_places.get(place, 0) + 1
            break
    return chosen
