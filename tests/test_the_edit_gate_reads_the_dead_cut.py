"""The edit gate reads the cut that was made, not the one that was planned (Jekyll ep01: G-DEAD
removed shots and slowed their neighbours, work/dead_cuts.json says so, and the gate still
measured every planned row and boundary).  Pure data, no ffmpeg, $0."""
from __future__ import annotations

import json

from scripts.episode import qc
from studio import edit_gate as gate


def placed() -> dict:
    shots = [{"index": i, "seconds": 2.0, "t_start": 2.0 * (i - 1)} for i in (1, 2, 3, 4)]
    return {"shots": shots, "duration_s": 8.0}


def records() -> list[dict]:
    return [{"index": i, "rel_path": f"takes/r2v/T{i:02d}.mp4", "shots": [i]} for i in (1, 2, 3, 4)]


PLAN = {"cut": [2], "seconds": {1: 3.0}, "room": {}}


def test_a_cut_shot_loses_its_row_and_its_boundary():
    p, r = gate.dead_view(placed(), records(), PLAN)
    assert [x["index"] for x in r] == [1, 3, 4]
    assert [s["index"] for s in p["shots"]] == [1, 3, 4]
    assert [len(gate.segment_plan(p, r))] == [3]


def test_a_slowed_neighbour_takes_its_new_length_and_the_next_start_moves():
    p, _ = gate.dead_view(placed(), records(), PLAN)
    assert [(s["seconds"], s["t_start"]) for s in p["shots"]] == [(3.0, 0.0), (2.0, 3.0), (2.0, 5.0)]
    assert qc.planned_cuts(p) == [3.0, 5.0]


def test_a_take_run_is_cut_or_scaled_as_one():
    run = [{"index": 1, "rel_path": "a", "shots": [1, 2]}, {"index": 3, "rel_path": "b", "shots": [3, 4]}]
    p, r = gate.dead_view(placed(), run, {"cut": [], "seconds": {1: 6.0}, "room": {}})
    assert [s["seconds"] for s in p["shots"]] == [3.0, 3.0, 2.0, 2.0]
    p, r = gate.dead_view(placed(), run, {"cut": [3], "seconds": {}, "room": {}})
    assert [x["index"] for x in r] == [1] and [s["index"] for s in p["shots"]] == [1, 2]


def test_no_dead_cuts_file_is_no_change(tmp_path):
    assert qc.dead_plan_of(tmp_path) is None
    assert gate.dead_view(placed(), records(), None) == (placed(), records())


def test_the_plan_is_read_from_the_work_folder(tmp_path):
    (tmp_path / "dead_cuts.json").write_text(json.dumps(PLAN), encoding="utf-8")
    assert qc.dead_plan_of(tmp_path)["cut"] == [2]
