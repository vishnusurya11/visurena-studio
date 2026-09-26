"""C5 (decision 2026-09-25): `gpu_seconds` on the work-order row comes from the
unit's `timing.jsonl` -- every row of a GPU stage, retries and failures
included, because a retry is GPU time too.  The file's stage names predate the
registry, so an explicit table maps each one to a step id and a GPU flag; a
name the table does not know is REPORTED by `unmapped`, never summed, never
guessed.  Nothing here touches a GPU or reads the library.
"""
from __future__ import annotations

import json

import pytest

from studio import timing_sum

# The names a real file uses (every episodes/*/timing.jsonl in the library on
# 2026-09-26), so a name the studio actually writes can never fall unmapped.
REAL_NAMES = [
    "assemble", "bind", "dossier", "eye_review", "frames", "grids", "lines",
    "no_last_frame", "panel_content", "panel_dq", "panels", "places", "prompts",
    "qc", "respot", "sheets", "speaker_check", "strip", "take_content", "take_dq",
    "takes", "timeline", "title",
]


def _write(home, rows):
    home.mkdir(parents=True, exist_ok=True)
    with (home / "timing.jsonl").open("w", encoding="utf-8") as fh:
        for stage, seconds, ok in rows:
            fh.write(json.dumps({"stage": stage, "started": "2026-09-24T21:19:24",
                                 "ended": "2026-09-24T21:27:37", "seconds": seconds,
                                 "ok": ok, "note": ""}) + "\n")


def test_a_retrys_seconds_count_too(tmp_path):
    _write(tmp_path, [("takes", 100.0, True), ("takes", 40.5, True)])
    assert timing_sum.gpu_seconds_of(tmp_path) == pytest.approx(140.5)


def test_a_failed_pass_is_gpu_time_spent(tmp_path):
    _write(tmp_path, [("takes", 100.0, False)])
    assert timing_sum.gpu_seconds_of(tmp_path) == pytest.approx(100.0)


def test_a_non_gpu_stage_is_not_summed(tmp_path):
    _write(tmp_path, [("respot", 30.0, True), ("timeline", 0.2, True), ("grids", 60.0, True)])
    assert timing_sum.gpu_seconds_of(tmp_path) == pytest.approx(60.0)


def test_an_unknown_name_is_reported_not_summed(tmp_path):
    _write(tmp_path, [("warp_drive", 999.0, True), ("takes", 1.0, True), ("warp_drive", 1.0, True)])
    assert timing_sum.gpu_seconds_of(tmp_path) == pytest.approx(1.0)
    assert timing_sum.unmapped(tmp_path) == ["warp_drive"]


def test_a_unit_with_no_clock_has_zero_seconds_and_nothing_unmapped(tmp_path):
    assert timing_sum.gpu_seconds_of(tmp_path / "nowhere") == 0.0
    assert timing_sum.unmapped(tmp_path / "nowhere") == []


def test_every_name_a_real_file_uses_is_mapped():
    assert [n for n in REAL_NAMES if n not in timing_sum.STAGES] == []


def test_the_table_agrees_with_the_run_script_gpu_flags():
    """The truth of the flag is the `gpu=` each step passes to run_script."""
    assert timing_sum.is_gpu("takes") and timing_sum.is_gpu("grids") and timing_sum.is_gpu("lines")
    assert not timing_sum.is_gpu("panels") and not timing_sum.is_gpu("strip")
    assert not timing_sum.is_gpu("no_such_stage")


def test_seconds_group_by_registry_step(tmp_path):
    """C7 writes work_steps.seconds from this: the file's names folded to step ids."""
    _write(tmp_path, [("respot", 30.0, True), ("timeline", 0.2, True), ("takes", 5.0, True)])
    assert timing_sum.step_seconds_of(tmp_path) == {"05": pytest.approx(30.2), "09": pytest.approx(5.0)}


def test_a_legacy_name_with_no_step_today_still_counts_its_gpu_time(tmp_path):
    """`sheets` and `frames` were episode stages before refs and board existed."""
    _write(tmp_path, [("sheets", 10.0, True), ("frames", 5.0, True)])
    assert timing_sum.gpu_seconds_of(tmp_path) == pytest.approx(15.0)
    assert timing_sum.unmapped(tmp_path) == []
