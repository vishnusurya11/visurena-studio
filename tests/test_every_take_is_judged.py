"""A take nobody judged has not passed.

Audit item 6, measured 2026-09-22. QC's take rollup and the upload's
`failed_takes` both counted only the T*.dq.json reports that exist, so a take
that was rendered and never judged -- or re-rendered after it was judged --
simply was not counted, and the one irreversible step (publishing) could not
see it. The universe is the takes the render recorded in shots.json.
"""
import json
import os
import time

from studio.judged import unjudged_takes


def takes(tmp_path, indices, judged, passed=True):
    (tmp_path / "shots.json").write_text(json.dumps([{"index": i} for i in indices]))
    for i in indices:
        (tmp_path / f"T{i:02d}.mp4").write_bytes(b"mp4")
    time.sleep(0.01)
    for i in judged:
        (tmp_path / f"T{i:02d}.dq.json").write_text(json.dumps({"passed": passed}))
    return tmp_path


def test_every_take_judged_leaves_nothing(tmp_path):
    assert unjudged_takes(takes(tmp_path, [0, 1], [0, 1])) == []


def test_a_take_with_no_report_is_named(tmp_path):
    assert unjudged_takes(takes(tmp_path, [0, 1, 2], [0, 2])) == ["T01"]


def test_a_take_rendered_again_after_its_report_is_named(tmp_path):
    d = takes(tmp_path, [0], [0])
    later = time.time() + 5
    os.utime(d / "T00.mp4", (later, later))
    assert unjudged_takes(d) == ["T00"]


def test_no_shots_record_means_nothing_can_be_vouched_for(tmp_path):
    assert unjudged_takes(tmp_path) == ["no shots.json: no record of which takes exist"]
