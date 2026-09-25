"""The registry describes what a step does; a gate that a judge signs must say
so in the step's prose, so the desk (generated from the registry) and the
org chart name the judge, not a person."""
from __future__ import annotations

import yaml

from studio import registry

STAGE_OF = {"refs": "refs", "episode": "episode"}


def prose(stage: str) -> str:
    parts = []
    for step in registry.steps(stage):
        parts.append(step.get("desc", ""))
        parts += [sub.get("desc", "") for sub in step.get("substeps", [])]
    return "\n".join(parts).lower()


def test_every_judged_gate_is_named_in_its_stage_prose():
    with open(registry.ROOT / "gates.yaml", encoding="utf-8") as fh:
        gates = yaml.safe_load(fh)["gates"]
    for stage, rows in gates.items():
        if stage not in STAGE_OF:
            continue
        text = prose(stage)
        for gate, row in rows.items():
            judge = str(row.get("judge", "")).split("@")[0]
            if row.get("state") == "auto" and judge:
                assert judge.lower() in text, f"{stage}/{gate}: judge {judge!r} not in the registry prose"


def test_no_stage_prose_parks_on_a_person():
    for stage in STAGE_OF:
        text = prose(stage)
        assert "escalate" not in text, f"{stage}: the registry still says ESCALATE"
        assert "the owner's" not in text, f"{stage}: the registry still asks the owner"
