"""warp_labels joins measures.warp to labels a person signed (casebook owner.jsonl, an eye-patch
strip signed by the owner or the master eye).  A shipped take is a default PASS and take_eye
echoes the gate: neither is a label.  Hard Se is re-armed only at >= 80 % precision on owner
labels, as a sustained run of >= 12 frame-pairs with face_w < 0.10 (P07 item 10)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.episode import warp_labels as wl  # noqa: E402


def lab(take, verdict, by="owner"):
    return {"path": f"episodes/ep01/takes/r2v/{take}.mp4", "verdict": verdict, "verdict_by": by}


def test_an_owner_row_is_a_label_and_a_default_pass_is_not():
    got = wl.labels([lab("T07", "fault"), lab("T08", "pass", "default"), lab("T09", "pass", "agent")])
    assert got == {"T07": "fault"}


def test_take_eye_is_never_a_label_source():
    assert wl.labels([lab("T07", "fault", "take_eye")]) == {}


def test_a_strip_signed_by_a_person_or_the_master_eye_is_a_label():
    strips = [{"take": "T10", "verdict": "fault", "signed_by": "master_eye"},
              {"take": "T11", "verdict": "pass", "signed_by": "owner"},
              {"take": "T12", "verdict": "fault", "signed_by": "take_eye"}]
    assert wl.strip_labels(strips) == {"T10": "fault", "T11": "pass"}


def test_the_join_carries_the_logged_scores_and_skips_unlabelled_takes():
    dq = {"T07": {"S": -0.04, "Se": 4.16, "S_held": None, "face_w": 0.06, "eye_spans": [[3, 16]], "frames_eye": 14},
          "T08": {"S": 0.1}}
    rows = wl.join(dq, {"T07": "fault"})
    assert [r["take"] for r in rows] == ["T07"] and rows[0]["label"] == "fault" and rows[0]["Se"] == 4.16


def test_a_sustained_run_needs_twelve_pairs_and_a_small_face():
    assert wl.sustained({"eye_spans": [[3, 14]], "face_w": 0.06})
    assert not wl.sustained({"eye_spans": [[3, 13]], "face_w": 0.06})        # 11 pairs
    assert not wl.sustained({"eye_spans": [[3, 20]], "face_w": 0.2})
    assert not wl.sustained({"eye_spans": [], "face_w": 0.06})


def row(label, **m):
    return {"label": label, "eye_spans": [[0, 12]], "face_w": 0.05} | m


def test_precision_counts_sustained_takes_the_owner_called_a_fault():
    rows = [row("fault"), row("fault"), row("fault"), row("fault"), row("pass")]
    assert wl.precision(rows) == 0.8


def test_hard_se_is_rearmed_at_eighty_percent_and_not_below():
    ok = [row("fault")] * 4 + [row("pass")]
    assert wl.rearmed(ok) is True
    assert wl.rearmed([row("fault")] * 3 + [row("pass")] * 2) is False


def test_too_few_labels_never_rearm():
    assert wl.rearmed([row("fault")]) is False


def test_harvest_marks_a_shipped_take_as_a_default_not_a_judged_pass():
    from scripts.calibration import harvest_labels as hl
    rows = hl.take_rows("c", "ep01", {"take": 7, "file": "T07.mp4", "attempts": []}, {}, "src", "v1")
    assert rows[0].verdict_by == "default" and rows[0].machine["label_source"] == "shipped-default"
    assert wl.labels([rows[0].model_dump()]) == {}
