"""A take that shipped flagged (work/flagged_takes.json, contract K7) gets three extra eye frames
inside its shot, and the reader is asked which body parts are visible; a limb that is seen in one
frame of the shot and gone in another is an ADVISORY body fault naming the shot (D8: advisory until
the eval reaches recall .6 / precision .8).  Fake reader, $0."""
from __future__ import annotations

import json

import numpy as np

from studio.judges import master_eye as me

PLACED = {"duration_s": 20.0, "shots": [
    {"index": 1, "t_start": 0.0, "t_end": 10.0, "seconds": 10.0},
    {"index": 2, "t_start": 10.0, "t_end": 20.0, "seconds": 10.0}]}


def said(parts: str) -> str:
    return json.dumps({"landform": "flat", "people": 1, "lookalikes": 0, "text": False, "hour": "day",
                       "framing": "medium", "action": "stands", "parts": parts})


def test_flagged_takes_get_extra_frames(tmp_path):
    work = tmp_path / "takes" / "work"
    work.mkdir(parents=True)
    (work / "flagged_takes.json").write_text(json.dumps(
        [{"take": 2, "shot": [2], "seconds_in_master": 10.0, "slowed": False, "rows": ["warp"], "notes": [],
          "severity": "high"}]), encoding="utf-8")
    assert me.flagged_shots(tmp_path) == [2]
    base = me.sample_times(20.0, 8)
    times = me.with_extra(base, PLACED, [2])
    extra = [t for t in times if t not in base]
    assert len(extra) == 3 and all(10.0 <= t < 20.0 for t in extra) and times == sorted(times)


def test_no_flagged_file_is_no_extra_frames(tmp_path):
    assert me.flagged_shots(tmp_path) == []
    assert me.with_extra([1.0, 2.0], PLACED, []) == [1.0, 2.0]


def reads(*parts_per_frame, shot=2):
    return {shot: [me.Read(at=10.0 + i, shot=shot, parts=p) for i, p in enumerate(parts_per_frame)]}


def test_a_limb_that_vanishes_between_frames_of_one_shot_is_a_body_fault_naming_the_shot():
    got = me.body_faults(reads(["head", "torso", "arm", "hand"], ["head", "torso"], ["head", "torso", "arm"]), [2])
    assert len(got) == 1 and got[0].kind == "body" and got[0].where == "shot_02"
    assert got[0].evidence["shot"] == 2 and got[0].evidence["lost"] == ["arm", "hand"]
    assert got[0].severity == "low" and "body" not in me.MEASURED


def test_a_shot_that_keeps_its_limbs_is_clean_and_an_unflagged_shot_is_not_judged():
    full = ["head", "torso", "arm", "hand"]
    assert me.body_faults(reads(full, full, full), [2]) == []
    assert me.body_faults(reads(full, ["head"]), []) == []


def test_the_reader_answer_carries_the_visible_parts():
    read = me.read_frame(lambda f: said("head, torso, arm"), np.zeros((4, 4, 3), np.uint8), 1.0, 1)
    assert read.parts == ["head", "torso", "arm"]
    assert me.read_frame(lambda f: said(["head", "hand"]), np.zeros((4, 4, 3), np.uint8), 1.0, 1).parts == ["head", "hand"]


def test_the_ask_has_the_body_parts_field():
    from scripts.episode import step_11_qc
    assert '"parts"' in step_11_qc.ASK
