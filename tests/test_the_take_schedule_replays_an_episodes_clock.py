"""scripts/episode/take_schedule_replay.py reads an episode's own clock --
timing.jsonl (the stage rows), takes/r2v/phases.jsonl (each render's seconds)
and ladder.json (each round's faults) -- and projects step 09's wall time
under the two lanes against today's serial order (studio/take_schedule).
Pure over the rows: the test feeds them, no file, no GPU."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("take_schedule_replay", ROOT / "scripts/episode/take_schedule_replay.py")
replay = importlib.util.module_from_spec(spec)
sys.modules["take_schedule_replay"] = replay
spec.loader.exec_module(replay)


def row(stage: str, seconds: float, note: str = "") -> dict:
    return {"stage": stage, "seconds": seconds, "note": note}


ROWS = [row("panel_eye", 170.0),
        row("takes", 0.8, "--from-refs"),                       # a resume that rendered nothing
        row("takes", 330.0, "--from-refs --no-ends --approved=render"),
        row("take_dq", 90.0), row("take_content", 120.0), row("strip", 6.0), row("take_eye", 40.0),
        row("takes", 230.0, "--from-refs --approved=render --retake=1,2 --why=batched_cures: gait, content"),
        row("take_dq", 120.0, "1 2 --attempts"), row("take_content", 80.0, "1 2"), row("take_eye", 40.0),
        row("assemble", 7.0)]
PHASES = [{"take": 0, "prompt_s": 100.0}, {"take": 1, "prompt_s": 110.0}, {"take": 2, "prompt_s": 115.0},
          {"take": 1, "prompt_s": 105.0}, {"take": 2, "prompt_s": 120.0}]
LADDER = [{"faults": {"1": ["gait"], "2": ["content"]}}]


def test_the_cycles_are_round_zero_and_each_retake_round_after_it():
    got = replay.step09_cycles(ROWS)
    assert [len(c) for c in got] == [5, 4]
    assert got[0][0]["seconds"] == 330.0 and got[1][-1]["stage"] == "take_eye"


def test_a_resume_between_rounds_is_not_a_round_and_round_two_is_found_past_it():
    later = [row("prompts", 1.0), row("takes", 250.0, "--from-refs --approved=render"), row("take_dq", 80.0),
             row("takes", 240.0, "--retake=1 --why=batched_cures: gait --last"), row("take_dq", 300.0, "1 --attempts"),
             row("take_content", 70.0, "1"), row("take_eye", 45.0), row("qc", 50.0)]
    got = replay.step09_cycles(ROWS + later)
    assert [len(c) for c in got] == [5, 4, 4] and got[2][0]["seconds"] == 240.0


def test_each_round_reads_its_renders_off_the_phase_rows_in_order():
    first, later = replay.renders(PHASES, [[1, 2]])
    assert first == ((0, 100.0), (1, 110.0), (2, 115.0))
    assert later == [((1, 105.0), (2, 120.0))]


def test_a_take_is_early_when_its_dq_rows_alone_order_a_render():
    assert replay.early_of({"1": ["gait"], "2": ["content"], "3": ["frozen-whole", "content"],
                            "4": ["lip-sync", "tail"]}) == frozenset({1, 3})


def test_the_costs_are_the_episodes_own_seconds():
    rounds, costs = replay.model(replay.step09_cycles(ROWS), PHASES, LADDER, vl_load_s=60.0)
    assert costs.dq_s == pytest.approx(30.0) and costs.dq_retake_s == pytest.approx(60.0)
    assert costs.content_s == pytest.approx(20.0) and costs.eye_s == pytest.approx(40.0)
    assert costs.launch_s == pytest.approx(5.0)            # 330 s of row over 325 s of renders
    assert rounds.early == frozenset({1}) and rounds.round2 == ()


def test_the_projection_never_reads_longer_than_the_serial_model():
    got = replay.project(ROWS, PHASES, LADDER, vl_load_s=60.0)
    assert got["measured_s"] == pytest.approx(330 + 90 + 120 + 6 + 40 + 230 + 120 + 80 + 40)
    assert got["overlapped_s"] < got["serial_s"] and got["overlap_only_s"] <= got["serial_s"]
