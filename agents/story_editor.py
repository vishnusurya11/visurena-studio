"""Story editor — what survives, and in what order (screenplay 02_02). ONE call/target.

Adaptation is fixed-budget allocation, not compression: every measured screenplay lands
in 22-33k words regardless of source size. A longer novel does not get a longer film,
it gets a higher cut rate. The agent is TOLD the budget; code MEASURES the result.
"""

from __future__ import annotations

import json
from pathlib import Path

from studio import llm
from studio.screenplay_spec import ScreenplayPlan

TIER = "reasoning"
SKILL_PATH = Path(__file__).parent / "skills" / "story_editor.md"

INDEX_FIELDS = ("chapter", "scene", "type", "location_id", "time_of_day",
                "story_day", "cast", "speaking", "summary")


def load_skill() -> str:
    return SKILL_PATH.read_text(encoding="utf-8")


def scene_index(scenes: list[dict], summary_words: int = 40) -> list[dict]:
    """~40 words per scene. The whole book has to fit in one prompt or the editor
    cannot see the shape it is being asked to cut."""
    index = []
    for scene in scenes:
        row = {k: scene.get(k) for k in INDEX_FIELDS}
        row["summary"] = " ".join((scene.get("summary") or "").split()[:summary_words])
        row["dialogue_lines"] = len(scene.get("dialogue") or [])
        index.append(row)
    return index


def plan(dossier: dict, target: dict, usage: dict | None = None) -> ScreenplayPlan:
    """Decide which scenes exist, grouped into sequences, inside a hard budget."""
    payload = {
        "target": target,
        "scenes": scene_index(dossier["scenes"]),
        "characters": [{"id": c["id"], "name": c["name"], "role": c.get("role")}
                       for c in dossier["characters"]],
        "locations": [{"id": loc["id"], "name": loc["name"]}
                      for loc in dossier["locations"]],
    }
    prompt = (f"{load_skill()}\n\n--- THE WHOLE BOOK, ONE LINE PER SCENE ---\n"
              f"{json.dumps(payload, ensure_ascii=False)}\n\n"
              f"Return the plan. Every source scene is in a beat or in `omitted`.")
    return llm.structured(TIER, prompt, ScreenplayPlan, usage=usage)
