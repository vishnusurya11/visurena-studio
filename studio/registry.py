"""The registry, read: stages.yaml is the org chart the code runs.

Every runner asks here for its stage's steps, its unit of work and what it
requires, instead of hard-coding a sibling stage and a step id.  Two keys are
optional on a stage and default for the stages written before they existed:

    unit:      the grain of the stage's production id, e.g. [book, chapter];
               default [book].  The events `unit` column carries the value.
    requires:  "<stage>/<step_id>" entries that must be `completed` before a
               unit of this stage is ready; default none.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "stages.yaml"
DEFAULT_UNIT = ["book"]


@lru_cache(maxsize=4)
def _load(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)["stages"]


def load(path: Path = PATH) -> dict:
    """Every stage, in file order."""
    return _load(str(path))


def stage_names(path: Path = PATH) -> list[str]:
    return list(load(path))


def stage(name: str, path: Path = PATH) -> dict:
    stages = load(path)
    if name not in stages:
        raise ValueError(f"unknown stage {name!r}; registered: {list(stages)}")
    return stages[name]


def steps(name: str, path: Path = PATH) -> list[dict]:
    return list(stage(name, path).get("steps") or [])


def unit_of(name: str, path: Path = PATH) -> list[str]:
    return list(stage(name, path).get("unit") or DEFAULT_UNIT)


def requires_of(name: str, path: Path = PATH) -> list[str]:
    return list(stage(name, path).get("requires") or [])
