"""The face replay's rows and counts (2026-10-21_ep02_proof DESIGN 4.1, package P6).

Pure helpers over named records: the take each index held at the first master (by the files'
own times, restored from attempts/ where a later repair displaced it), the first-pass attempts
record with every repair-era refine and tiny-face round taken out, one row per (take, person),
the pre-registered kill on crop requests the fake ComfyUI did not answer `exact` (P3's classes:
exact, substituted, canned), decision agreement with the repair, the outside-the-face invariant
and the SR-1 estimate."""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pytest

from studio.rehearsal import face_rows as rows


def touch(path: Path, body: bytes, mtime: float) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)
    os.utime(path, (mtime, mtime))
    return path


def test_tiers_follow_the_design_lines():
    assert [rows.tier(p) for p in (None, 10.7, 39.9, 40.0, 120.0, 120.1)] == [None, "tiny", "tiny", "mid", "mid", "big"]


def test_the_iter1_take_is_the_newest_file_rendered_by_the_first_master(tmp_path):
    room = tmp_path / "r2v"
    touch(room / "attempts" / "T01_fail1.mp4", b"iter1", 100.0)     # displaced by the repair
    touch(room / "T01.mp4", b"repair draw", 300.0)
    touch(room / "attempts" / "T02_fail1.mp4", b"first render", 50.0)
    touch(room / "T02.mp4", b"retake before iter1", 120.0)
    assert rows.iter1_take(room, 1, cutoff=200.0) == (room / "attempts" / "T01_fail1.mp4", [])
    assert rows.iter1_take(room, 2, cutoff=200.0) == (room / "T02.mp4", [room / "attempts" / "T02_fail1.mp4"])
    assert rows.iter1_take(room, 3, cutoff=200.0) == (None, [])


def test_the_first_pass_attempts_drop_every_refine_and_tiny_face_round():
    doc = {"face_refine.T06": {"rounds": 2, "seconds": 0.0}, "tiny_face.T01": {"rounds": 1, "seconds": 0.0},
           "retakes": {"rounds": 2, "seconds": 154.1}, "wall.09": {"rounds": 8, "seconds": 7438.8}}
    ladder = {"rounds": [{"at": 100.0}, {"at": 500.0}]}
    out = rows.first_pass_attempts(doc, ladder, cutoff=200.0)
    assert set(out) == {"retakes", "wall.09"} and out["retakes"]["rounds"] == 1
    assert rows.first_pass_ladder(ladder, cutoff=200.0) == {"rounds": [{"at": 100.0}]}


def test_the_kill_fires_when_over_half_the_answers_are_not_exact_in_p3s_classes():
    assert rows.kill(["exact", "canned", "substituted"])["real_run"]
    said = rows.kill(["exact", "exact", "canned", "substituted"])
    assert not said["real_run"] and said == {"requests": 4, "exact": 2, "substituted": 1, "canned": 1,
                                             "not_exact": 2, "share": 0.5, "real_run": False}
    assert rows.kill([])["real_run"]                # no request is no evidence
    with pytest.raises(ValueError):
        rows.kill(["unrecorded"])                   # only the fake's own vocabulary is counted


def person(who, kept, eye_src=40.0, eye_ref=90.0, min_px=50.0, why="kept"):
    return {"who": who, "kept": kept, "why": why, "min_px": min_px, "face_px": min_px + 2,
            "crop": f"refine/T05_p0.mp4", "measures": {"eye_src": eye_src, "eye_ref": eye_ref,
                                                       "flick_ref": 3.2, "id_ref": 0.61}}


def test_a_row_carries_the_design_columns():
    replay = {"T05": {"status": "refined", "take_sha8": "aa", "people": [person("enfield", True)]}}
    iter3 = {"T05": {"status": "unrefined", "take_sha8": "aa", "people": [person("enfield", False, eye_src=41.0)]}}
    out = rows.take_rows(5, replay, iter1={}, iter3=iter3, selected={5}, matches={("T05", "enfield"): "exact"},
                         outside={("T05", "enfield"): 0.0})
    assert out == [{"take": "T05", "who": "enfield", "px": 50.0, "tier": "mid", "selected": True, "refined": True,
                    "accepted": True, "why": "kept", "eye_cel_iter1": None, "eye_cel_replay": 90.0,
                    "eye_cel_iter3": 41.0, "outside_moved": 0.0, "flicker": 3.2, "id_ref": 0.61, "match": "exact",
                    "iter1_basis": "overwritten"}]


def test_a_selected_take_with_no_person_is_one_row_saying_why():
    replay = {"T00": {"status": "all_readable", "take_sha8": "bb", "people": []}}
    out = rows.take_rows(0, replay, iter1={}, iter3={}, selected={0}, matches={}, outside={})
    assert len(out) == 1 and out[0]["who"] is None and out[0]["why"] == "all_readable" and not out[0]["refined"]


def test_decision_agreement_counts_the_takes_the_repair_decided():
    replay = {"T05": {"status": "refined"}, "T06": {"status": "unrefined"}, "T09": {"status": "unrefined"}}
    repair = {"T05": {"status": "refined"}, "T06": {"status": "refined"}, "T09": {"status": "unrefined"},
              "T24": {"status": "no_faces"}}
    said = rows.agreement(replay, repair, ["T05", "T06", "T09", "T13"])
    assert (said["agree"], said["n"]) == (2, 4)
    assert {"take": "T13", "replay": None, "repair": None, "agree": False} in said["rows"]


def test_outside_moved_counts_changed_pixels_outside_the_allowed_core():
    before = np.zeros((4, 4, 3), np.uint8)
    after = before.copy()
    after[0, 0] = 9                          # inside the core: allowed
    allowed = np.zeros((4, 4), bool)
    allowed[0, 0] = True
    assert rows.outside_moved(before, after, allowed) == 0.0
    after[3, 3] = 9
    assert rows.outside_moved(before, after, allowed) == pytest.approx(1 / 15)


def test_the_sr1_estimate_sums_measured_gpu_and_says_when_only_a_price_exists():
    entries = {"T05": {"gpu_s_priced": 41.8}, "T06": {"gpu_busy_s": 80.0, "gpu_s_priced": 60.0}}
    said = rows.sr1_estimate(entries, ["T05", "T06", "T07"])
    assert said == {"takes": 3, "measured_s": 80.0, "measured_takes": 1, "priced_s": 41.8, "priced_takes": 1,
                    "unknown_takes": ["T07"], "estimate_s": 121.8}


def test_the_noise_band_is_the_largest_change_of_a_repeat_or_a_one_frame_shift():
    first, again = {4: 10.0, 8: 12.0}, {4: 10.0, 8: 12.0}
    near = {3: 9.0, 5: 11.0, 7: 12.5, 9: 15.0}
    assert rows.noise_band(first, again, near) == {"repeat": 0.0, "shift": 3.0, "reads": 2}


def test_the_noise_band_pairs_readings_by_frame_never_by_position():
    """crop_eyes skips a frame with no face box: frame 5 unread must not pair frame 8 with frame 3."""
    first, again = {4: 10.0, 8: 50.0}, {4: 10.0, 8: 50.0}
    near = {3: 10.5, 9: 51.0}                       # 5 and 7 had no face box
    assert rows.noise_band(first, again, near) == {"repeat": 0.0, "shift": 1.0, "reads": 2}


def test_a_record_is_read_by_name_and_a_missing_one_is_its_default(tmp_path):
    (tmp_path / "a.json").write_text('{"x": 1}', encoding="utf-8")
    assert rows.read_json(tmp_path / "a.json", {}) == {"x": 1}
    assert rows.read_json(tmp_path / "missing.json", []) == []


@pytest.mark.parametrize("cls", ["canned", "substituted"])
def test_a_row_the_fake_did_not_answer_exact_carries_no_decision_its_render_made(cls):
    replay = {"T06": {"status": "unrefined", "people": [person("hyde", False, eye_src=20.4, why="faces 0 != 1")]}}
    (row,) = rows.take_rows(6, replay, iter1={}, iter3={}, selected={6}, matches={("T06", "hyde"): cls},
                            outside={})
    assert row["refined"] and row["match"] == cls and row["px"] == 50.0 and row["tier"] == "mid"
    assert (row["accepted"], row["eye_cel_replay"], row["flicker"], row["id_ref"]) == (None, None, None, None)
    assert row["why"].startswith(f"{cls}: the gate read a render that is not this crop's")


def test_selection_agreement_compares_the_people_each_take_was_tracked_for():
    replay = {"T05": {"people": [{"who": "enfield"}]}, "T09": {"people": [{"who": "enfield"}, {"who": "hyde"}]},
              "T00": {"people": []}}
    repair = {"T05": {"people": [{"who": "enfield"}]}, "T09": {"people": [{"who": "hyde"}]}, "T00": {"people": []},
              "T01": {"people": [{"who": "utterson"}]}}
    said = rows.selection_agreement(replay, repair, ["T00", "T01", "T05", "T09"])
    assert (said["agree"], said["n"]) == (2, 4)
    assert next(r for r in said["rows"] if r["take"] == "T09") == {"take": "T09", "replay": ["enfield", "hyde"],
                                                                  "repair": ["hyde"], "agree": False}


def test_the_sr1_inputs_price_the_replays_crops_and_measure_only_the_real_record():
    replay = {"T05": {"take_sha8": "aa", "gpu_busy_s": 0.0, "gpu_s_priced": 41.8}}
    real = {"T05": {"take_sha8": "aa", "gpu_busy_s": 77.0}, "T06": {"take_sha8": "bb", "gpu_busy_s": 9.0}}
    assert rows.sr1_inputs(replay, real) == {"T05": {"gpu_s_priced": 41.8, "gpu_busy_s": 77.0}}
    assert rows.sr1_inputs(replay, {"T05": {"take_sha8": "zz", "gpu_busy_s": 77.0}}) == {"T05": {"gpu_s_priced": 41.8}}


def test_a_noise_band_over_no_reading_is_unmeasured_never_zero():
    assert rows.noise_band({}, {}, {}) == {"repeat": None, "shift": None, "reads": 0}
    assert rows.noise_band({4: 10.0}, {4: 10.0}, {})["shift"] is None
