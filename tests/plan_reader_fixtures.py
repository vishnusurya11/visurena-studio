"""What the plan critic's tests share: the canned readings under
tests/fixtures/llm, a brief with two chapter rows and a chapter text the
good reading's claim span is in, and the two scrubbed plans (known-good,
known-bad).  Nothing here names a book, a character or an episode.
"""
from __future__ import annotations

import json
from pathlib import Path

from studio.judges.plan import PlanReading

FIXTURES = Path(__file__).parent / "fixtures" / "llm"

CHAPTER = ("Two people met in a plain room at the end of the day. She set the cup on the "
           "table and he took the cup from her hand. You came back, then, after all this "
           "time, she said, and neither of them looked at the window.")

BRIEF = {"number": 3,
         "scenes": [{"n": 1, "summary": "Two people meet in a plain room."},
                    {"n": 2, "summary": "One hands the other a cup and speaks."}],
         "chapter_text": CHAPTER}


def reading(name: str) -> PlanReading:
    """One canned reading by its fixture name: good, no_turn, no_answer, dropped."""
    doc = json.loads((FIXTURES / f"plan_reading_{name}.json").read_text(encoding="utf-8"))
    return PlanReading.model_validate(doc)


def reading_dict(name: str) -> dict:
    return json.loads((FIXTURES / f"plan_reading_{name}.json").read_text(encoding="utf-8"))


def plan(name: str) -> dict:
    """One scrubbed plan by name: known_good, known_bad."""
    return json.loads((FIXTURES / f"plan_{name}.json").read_text(encoding="utf-8"))
