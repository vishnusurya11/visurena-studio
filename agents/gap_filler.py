"""Gap filler agent — place scenes the deterministic pipeline could not (step 04).

Code can interpolate an hour (between morning and evening lies afternoon) but it can
NEVER interpolate a place: the midpoint of two locations is meaningless. An agent that
reads the scene can.

Owner decision 2026-08-23: **every scene must get a location and a time** — downstream
consumers (the map video, per-location files, continuity checks) need a place for every
scene, so abstaining is not offered. The agent commits to the best-supported answer and
records its confidence and reasoning; answers are labelled `inferred` so they never
masquerade as stated evidence.
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

from studio import llm

TIER = "workhorse"
SKILL_PATH = Path(__file__).parent / "skills" / "gap_filler.md"


class Placement(BaseModel):
    location_id: str          # required — every scene happens somewhere
    time_of_day: str          # required — DAY or NIGHT, never UNKNOWN
    confidence: str
    reasoning: str


def load_skill() -> str:
    return SKILL_PATH.read_text(encoding="utf-8")


def _brief(scene: dict | None) -> dict | None:
    if not scene:
        return None
    return {"chapter": scene["chapter"], "scene": scene["scene"],
            "location_id": scene.get("location_id"),
            "location_text": scene.get("location_text"),
            "time_of_day": scene.get("time_of_day"),
            "clock": scene.get("clock"), "summary": scene.get("summary")}


def place(scene: dict, before: list[dict], after: list[dict],
          locations: dict, usage: dict | None = None) -> Placement:
    """Decide where and when one unresolved scene happens.

    `before`/`after` are windows of surrounding scenes (already resolved where
    possible), not just the immediate neighbours — a scene's place is often settled by
    the shape of the whole sequence rather than the one line either side."""
    catalogue = [{"id": lid, "name": loc["name"], "region": loc.get("region")}
                 for lid, loc in locations.items()]
    payload = {
        "scene_to_place": {**_brief(scene),
                           "characters": scene.get("characters", []),
                           "time_evidence": [e.get("text") for e in
                                             scene.get("time_evidence", [])][:8]},
        "scenes_before": [_brief(s) for s in before],
        "scenes_after": [_brief(s) for s in after],
        "canonical_locations": catalogue,
    }
    prompt = (f"{load_skill()}\n\n--- SCENE AND ITS SURROUNDING SEQUENCE ---\n"
              f"{json.dumps(payload, ensure_ascii=False)}\n\n"
              f"Give this scene a location and a time of day.")
    return llm.structured(TIER, prompt, Placement, usage=usage)
