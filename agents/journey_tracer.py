"""Journey tracer agent — turn a multi-place span into an ordered route (step 04).

Some spans are not one place. A Study in Scarlet opens with four paragraphs that carry
Watson from London to Netley to Bombay to Candahar to Maiwand to Peshawar to Portsmouth
to London across roughly two years. Asking "where is this scene?" of such a passage is
asking the wrong question: any single answer is wrong, because the passage's whole
subject is movement.

The gap filler still names the ONE most consequential place (some consumers need a
single point). This agent adds what that flattening loses — the ordered legs — so a
character's worldline shows them travelling rather than teleporting.

A leg is not a scene. Legs subdivide their parent scene's own slot on the time axis and
never spill into the next scene, so adding them can never reorder the book.
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

from studio import llm

TIER = "workhorse"
SKILL_PATH = Path(__file__).parent / "skills" / "journey_tracer.md"


class Leg(BaseModel):
    order: int                # 1-based, the order the text travels them
    location_id: str          # canonical id
    when: str                 # what the text says about when — its own words
    event: str                # one line: what happens on this leg
    time_of_day: str          # DAY or NIGHT


class Journey(BaseModel):
    is_journey: bool          # False when the span really is a single place
    primary_location_id: str  # the one place to use where only one is possible
    legs: list[Leg]
    reasoning: str


def load_skill() -> str:
    return SKILL_PATH.read_text(encoding="utf-8")


def _brief(scene: dict) -> dict:
    return {"chapter": scene["chapter"], "scene": scene["scene"],
            "location_id": scene.get("location_id"),
            "location_text": scene.get("location_text"),
            "time_of_day": scene.get("time_of_day"), "summary": scene.get("summary")}


def trace(scene: dict, text: str, before: list[dict], after: list[dict],
          locations: dict, usage: dict | None = None) -> Journey:
    """Break one span into the places it actually travels, in order.

    `text` is the span's own prose — unlike placement, this question cannot be answered
    from a summary, because the summary is exactly what flattened the route away."""
    catalogue = [{"id": lid, "name": loc["name"], "region": loc.get("region")}
                 for lid, loc in locations.items()]
    payload = {
        "span": {**_brief(scene), "type": scene.get("type"), "prose": text},
        "scenes_before": [_brief(s) for s in before],
        "scenes_after": [_brief(s) for s in after],
        "canonical_locations": catalogue,
    }
    prompt = (f"{load_skill()}\n\n--- THE SPAN AND ITS SURROUNDINGS ---\n"
              f"{json.dumps(payload, ensure_ascii=False)}\n\n"
              f"List the places this span travels, in order.")
    return llm.structured(TIER, prompt, Journey, usage=usage)
