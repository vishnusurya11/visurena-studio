"""The registry, read: stages.yaml is the org chart the code runs.

Every runner asks here for its stage's steps, its unit of work and what it
requires, instead of hard-coding a sibling stage and a step id.  Two keys are
optional on a stage and default for the stages written before they existed:

    unit:      the grain of the stage's production id, e.g. [book, chapter];
               default [book].  The events `unit` column carries the value.
    requires:  "<stage>/<step_id>" entries that must be `completed` before a
               unit of this stage is ready; default none.

Two keys are optional on a step (decision 2026-09-25, the Command Center):

    in:   book-relative globs the step reads, `{unit}` templated
          (episodes/{unit}/plan.json); a book-level file is plain (refs/refs.json).
    out:  the same for what the step writes.  A department's deliverable is
          its last step's first output.  A step declaring neither answers [].
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


def step(name: str, step_id: str, path: Path = PATH) -> dict:
    """One step's registry row, refused by id when the stage has no such step."""
    for entry in steps(name, path):
        if entry["id"] == step_id:
            return entry
    raise ValueError(f"unknown step {step_id!r} of stage {name!r}; "
                     f"registered: {[s['id'] for s in steps(name, path)]}")


def _templated(paths: list[str], unit: str | None) -> list[str]:
    """`{unit}` filled in when a unit is given; left as the template when not."""
    return [p.replace("{unit}", unit) if unit else p for p in paths]


def inputs_of(name: str, step_id: str, unit: str | None = None, path: Path = PATH) -> list[str]:
    """What the step reads, as book-relative globs; [] when undeclared."""
    return _templated(list(step(name, step_id, path).get("in") or []), unit)


def outputs_of(name: str, step_id: str, unit: str | None = None, path: Path = PATH) -> list[str]:
    """What the step writes, as book-relative globs; [] when undeclared."""
    return _templated(list(step(name, step_id, path).get("out") or []), unit)


def deliverable_of(name: str, unit: str | None = None, path: Path = PATH) -> str | None:
    """The department's deliverable: its last step's first output, or None
    when the stage declares no outputs."""
    entries = steps(name, path)
    if not entries:
        return None
    outs = outputs_of(name, entries[-1]["id"], unit, path)
    return outs[0] if outs else None
