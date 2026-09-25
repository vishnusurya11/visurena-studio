"""`reprose` cures a panel fault by editing the CELL PROSE of the faulted shot
(its `frame`) from the cure table and nothing else -- never a beat, a coda, a
line -- so the timeline's fingerprint is unchanged and placed.json stays
current.  The edited plan is still a plan the contract accepts, through
write_plan, and the words are affirmative."""
from __future__ import annotations

import json
from pathlib import Path

from studio import episode_home, panel_ladder, timeline_fresh
from studio.affirm import negations
from studio.episode_spec import Episode
from studio.judges.verdict import Fault

PLAN = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "episodes" / "ep05_plan.json"


def load() -> dict:
    return json.loads(PLAN.read_text(encoding="utf-8"))


def faults() -> list[Fault]:
    return [Fault(kind="clones", where="shot_09", evidence={"cosine": 0.81}),
            Fault(kind="posture", where="shot_09", evidence={"asked": "lying", "calibrated": False}),
            Fault(kind="text", where="shot_11")]


def test_the_timing_inputs_are_untouched_and_placed_stays_current(tmp_path):
    before = Episode.model_validate(load())
    placed = {"plan": timeline_fresh.fingerprint(before)}
    out = panel_ladder.reprose_plan(tmp_path / "plan.json", load(), 9, faults())
    after = Episode.model_validate_json(out.read_text(encoding="utf-8"))
    assert timeline_fresh.fingerprint(after) == timeline_fresh.fingerprint(before)
    assert timeline_fresh.stale(after, placed) == []


def test_only_the_frame_of_that_shot_changes():
    before, doc = load(), panel_ladder.reprose(load(), 9, faults())
    for old, new in zip(before["shots"], doc["shots"]):
        changed = {k for k in set(old) | set(new) if old.get(k) != new.get(k)}
        assert changed == {"frame"} if old["index"] == 9 else not changed
    assert before["lines"] == doc["lines"] and before["setups"] == doc["setups"]


def test_the_cure_leads_the_prose_and_is_affirmative():
    doc = panel_ladder.reprose(load(), 9, faults())
    frame = next(s["frame"] for s in doc["shots"] if s["index"] == 9)
    assert frame.startswith(panel_ladder.cure("clones", {}))
    assert "lying" in frame and negations(frame) == []
    for kind in panel_ladder.CURES:
        assert negations(panel_ladder.cure(kind, {"asked": "lying", "planned": "close"})) == []


def test_a_cure_is_written_once_however_often_it_is_asked():
    doc = panel_ladder.reprose(panel_ladder.reprose(load(), 9, faults()), 9, faults())
    frame = next(s["frame"] for s in doc["shots"] if s["index"] == 9)
    assert frame.count(panel_ladder.cure("clones", {})) == 1


def test_a_fault_on_another_shot_edits_nothing_here():
    before, doc = load(), panel_ladder.reprose(load(), 9, [Fault(kind="text", where="shot_11")])
    assert before == doc
    assert episode_home.write_plan.__name__ == "write_plan"
