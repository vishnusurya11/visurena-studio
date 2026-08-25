"""Shot designer — one beat's frozen element stream into shots (screenplay 03_02).

A separate agent from the screenwriter because shots attach to element INDICES in an
already-frozen stream, so they merge mechanically by index — and the camera language
can be re-run alone when it is wrong, without paying to rewrite a line of dialogue.

Text is a lossy actuator: instructed camera motion lands 27-62% of the time
(VBench-2.0). The capability is latent; the prompt is the bottleneck.
"""

from __future__ import annotations

import json
from pathlib import Path

from studio import llm
from studio.screenplay_spec import ShotPlan

TIER = "workhorse"
SKILL_PATH = Path(__file__).parent / "skills" / "shot_designer.md"


def load_skill() -> str:
    return SKILL_PATH.read_text(encoding="utf-8")


def numbered(elements: list[dict]) -> list[dict]:
    """Shots key on index, so the agent must see the index it is keying on."""
    return [{"index": i, "kind": e["kind"], "character": e.get("character"),
             "text": e["text"]} for i, e in enumerate(elements)]


def design(elements: list[dict], slug: dict, location_visual: str | None,
           usage: dict | None = None) -> ShotPlan:
    """Where the camera is, over an element stream nobody may rewrite."""
    payload = {"slug": slug, "location_visual": location_visual,
               "elements": numbered(elements)}
    prompt = (f"{load_skill()}\n\n--- THE FROZEN ELEMENT STREAM ---\n"
              f"{json.dumps(payload, ensure_ascii=False)}\n\n"
              f"Return shots tiling every element index, with no gaps or overlaps.")
    return llm.structured(TIER, prompt, ShotPlan, usage=usage)
