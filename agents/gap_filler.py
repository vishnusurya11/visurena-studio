"""Gap filler agent — place scenes the deterministic pipeline could not (step 04).

Code can interpolate an hour (between morning and evening lies afternoon) but it can
NEVER interpolate a place: the midpoint of two locations is meaningless. An agent that
reads the scene can. Called only for the handful of gaps, and its answers are labelled
`inferred` so they never masquerade as stated evidence — including the answer "this
scene happens nowhere", which is correct for summary sweeps and reflections.
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

from studio import llm

TIER = "workhorse"
SKILL_PATH = Path(__file__).parent / "skills" / "gap_filler.md"


class Placement(BaseModel):
    location_id: str | None
    time_of_day: str
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


def place(scene: dict, previous: dict | None, following: dict | None,
          locations: dict, usage: dict | None = None) -> Placement:
    """Infer where (and when) one unresolved scene happens."""
    catalogue = [{"id": lid, "name": loc["name"], "region": loc.get("region")}
                 for lid, loc in locations.items()]
    payload = {
        "scene_to_place": {**_brief(scene),
                           "characters": scene.get("characters", []),
                           "time_evidence": [e.get("text") for e in
                                             scene.get("time_evidence", [])][:8]},
        "previous_scene": _brief(previous),
        "following_scene": _brief(following),
        "canonical_locations": catalogue,
    }
    prompt = (f"{load_skill()}\n\n--- SCENE AND ITS NEIGHBOURS ---\n"
              f"{json.dumps(payload, ensure_ascii=False)}\n\nPlace this scene.")
    return llm.structured(TIER, prompt, Placement, usage=usage)
