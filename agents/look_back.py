"""Look-back agent -- a drawn picture read against its own prompt (refs 02_03,
episode 03_02).

Its model is a PICTURE model: the local vision model through comfy.run_text
(studio/look_back.py), not a text tier, so this agent never calls
llm.structured( -- the text gateway has no eyes.  What it keeps of the agent
convention is the half that matters: the model LISTS in a closed shape and code
judges (`studio.look_back.diff`); it is never asked a yes/no.  The reader is
injectable so no test touches the GPU.

Advisory this pass (decision 2026-09-24, D8): no calibration exists yet, so a
miss is logged by the step that called and nothing is refused.
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable

from studio import look_back
from studio.look_back import LookReading  # noqa: F401  (the reading, re-exported)

TIER = "vlm"
"""Not a models.yaml tier: the local vision model on ComfyUI, $0."""
SKILL_PATH = Path(__file__).parent / "skills" / "look_back.md"


def load_skill() -> str:
    return SKILL_PATH.read_text(encoding="utf-8")


def look(picture: Path, prompt: str, reader: Callable | None = None, must=()) -> LookReading:
    """What the picture shows, and which of the prompt's nouns it does not."""
    return look_back.read(Path(picture), prompt, reader=reader, must=must)
