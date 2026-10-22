"""The deterministic CPU judges are registered for the bench (fleet H ruling A22, A20).

stillness (frozen-whole), warp_gate (G-WARP) and the mouth lag row re-judge a
casebook row from the values its dq record kept, through the SHIPPED verdict
functions, and say "not measured" on a row without them.  Each entry carries
its standing: stillness is uncertified and log only (fleet H skeptic F1: its
flow core under-reads 33-58 % on a dark, flat frame); the mouth lag row is
advisory, because no mouth reader passes the exam.

A NEW VLM second-opinion reader (A20) may flag, never refuse, until its
calibration meets PREREG B1 rule 4 (sensitivity and specificity one-sided CP
lower bounds of 0.80 on 30 owner faults and 30 owner passes) and the owner
says go.  The panel_content reader that exists today is untouched.
"""
from studio import intervals
from studio.casebook import Row
from studio.judges import registry

GATES = [{"name": "frozen-whole", "value": 0.8, "ok": False, "hard": True, "note": "80% static, run 6.0s HARD: the whole frame stands still", "penalty": 48.0}]
WARP = {"state": "fail", "S": 3.1, "Se": 1.0, "share": 0.9, "spans": [[3, 9]]}
LAG = {"measured": True, "lag_frames": 6, "lag_s": 0.25, "corr": 0.6}


def take(take_dq: dict) -> Row:
    return Row(codex="c", unit="ep01", kind="take", path="episodes/ep01/takes/r2v/T01.mp4", verdict="fault",
               fault_class="frozen_share", verdict_by="owner", machine={"take_dq": take_dq})


def test_each_new_judge_says_not_measured_on_a_row_without_its_inputs():
    for name in ("stillness", "warp_gate", "mouth_lag"):
        said = registry.get(name).judge(take({}))
        assert said == {"refused": False, "classes": [], "values": {"note": "not measured"}}, name


def test_stillness_re_judges_the_stored_share_against_the_shipped_wall():
    said = registry.get("stillness").judge(take({"gates": GATES, "seconds": 6.0}))
    assert said["refused"] is True and said["classes"] == ["frozen_share"]
    short = registry.get("stillness").judge(take({"gates": GATES, "seconds": 3.0}))
    assert short["refused"] is False
    planned = [g | {"note": "80% static, run 6.0s (planned still)"} for g in GATES]
    assert registry.get("stillness").judge(take({"gates": planned, "seconds": 6.0}))["refused"] is False


def test_warp_and_mouth_lag_re_judge_their_stored_measures():
    assert registry.get("warp_gate").judge(take({"measures": {"warp": WARP}}))["classes"] == ["blur_warp"]
    calm = WARP | {"state": "pass", "S": 0.5}
    assert registry.get("warp_gate").judge(take({"measures": {"warp": calm}}))["refused"] is False
    assert registry.get("mouth_lag").judge(take({"measures": {"lag": LAG}}))["classes"] == ["lip_lag"]
    near = LAG | {"lag_frames": 1}
    assert registry.get("mouth_lag").judge(take({"measures": {"lag": near}}))["refused"] is False


def test_every_entry_says_its_standing():
    assert registry.get("stillness").standing.startswith("uncertified")
    assert registry.get("mouth_lag").standing.startswith("advisory")
    assert registry.get("take_verdict").standing == "shipped"


def refuses_all(row):
    return {"refused": True, "classes": ["landform"], "values": {}}


def test_a_vlm_reader_without_a_calibration_record_cannot_refuse():
    entry = registry.vlm_entry("landmark_vlm", "panel", ("landform",), "abcdef01", refuses_all)
    said = entry.judge(take({}))
    assert said["refused"] is False and said["values"]["flags"] == ["landform"]
    assert entry.standing.startswith("flag only")


def test_a_vlm_reader_refuses_only_past_rule_4_and_the_owners_go():
    strong = {"faults": 30, "caught": 30, "passes": 30, "cleared": 30, "owner_go": True}
    assert intervals.cp_lower(30, 30) >= 0.80
    assert registry.vlm_entry("v", "panel", ("landform",), "abcdef01", refuses_all, strong).judge(take({}))["refused"]
    for weak in (strong | {"owner_go": False}, strong | {"faults": 29, "caught": 29}, strong | {"cleared": 24}):
        entry = registry.vlm_entry("v", "panel", ("landform",), "abcdef01", refuses_all, weak)
        assert entry.judge(take({}))["refused"] is False, weak
