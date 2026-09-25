"""`replan_cell` re-aims a shot whose content fault repeated on a fresh seed:
it edits the cell's prose and its motion only -- never a beat, a coda, a line
-- so the timeline's fingerprint is unchanged and placed.json stays current
(GATES: "a reworded frame does not stale it").  The edited plan is still a
plan the contract accepts, through write_plan."""
from __future__ import annotations

import json
from pathlib import Path

from studio import episode_home, take_ladder, timeline_fresh
from studio.episode_spec import Episode
from studio.judges.verdict import Fault

PLAN = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "episodes" / "ep05_plan.json"
CELL = ("frame", "at_rest", "motion", "extras")


def load() -> dict:
    return json.loads(PLAN.read_text(encoding="utf-8"))


def faults() -> list[Fault]:
    return [Fault(kind="content", where="T09", evidence={"hard": True, "repeated": True},
                  note="2 figure(s) for 1 declared (1 cast + 0 extras), 0 of them copies of another")]


def test_the_timing_inputs_are_untouched_and_the_plan_still_validates(tmp_path):
    before = Episode.model_validate(load())
    doc = take_ladder.replan(load(), 9, faults())
    out = episode_home.write_plan(tmp_path / "plan.json", doc)
    after = Episode.model_validate_json(out.read_text(encoding="utf-8"))
    assert timeline_fresh.fingerprint(after) == timeline_fresh.fingerprint(before)
    assert timeline_fresh.stale(after, {"plan": timeline_fresh.fingerprint(before)}) == []


def test_only_the_cell_fields_of_that_shot_change():
    before, doc = load(), take_ladder.replan(load(), 9, faults())
    for old, new in zip(before["shots"], doc["shots"]):
        changed = {k for k in set(old) | set(new) if old.get(k) != new.get(k)}
        assert changed <= set(CELL) if old["index"] == 9 else not changed
    assert before["lines"] == doc["lines"] and before["setups"] == doc["setups"]


def test_a_repeated_content_fault_locks_the_camera_on_the_body_verb():
    doc = take_ladder.replan(load(), 9, faults())
    motion = next(s["motion"] for s in doc["shots"] if s["index"] == 9)
    assert motion.startswith("The camera holds a locked-off frame;")
    assert take_ladder.wants(faults()[0], "replan_cell", motion)
    assert not take_ladder.wants(Fault(kind="content", where="T09", evidence={"repeated": False}), "replan_cell")
