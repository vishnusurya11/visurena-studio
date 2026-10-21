"""The eye instrument's calibration gate (2026-10-21_ep02_proof DESIGN 4.2, R6).

An instrument whose agreement with the OWNER's labels has a Wilson 95 % lower bound under 0.70 over
at least 30 labelled faces measures nothing: every eye_cel row it wrote prints INSTRUMENT FAILED.
Labels come only from the owner's `owner` field of a review/face_labels_<sha8>.json file; the
production EYE judge's `eye` field may be MEASURED as a second candidate, never used as a label."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from studio.rehearsal import instrument_gate as ig


def label_doc(owner: list[str], eye: list[str] | None = None) -> dict:
    eye = eye or ["clear"] * len(owner)
    crops = [{"crop": f"faces_x/c{k:02d}.png", "take": f"T{k:02d}", "px": 50.0, "eye": e, "owner": o}
             for k, (o, e) in enumerate(zip(owner, eye))]
    return {"sha8": "0db3d8d9", "labels": ["good", "bad"], "crops": crops}


def write_labels(folder: Path, doc: dict, name: str = "face_labels_0db3d8d9.json") -> Path:
    path = folder / "review" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc), encoding="utf-8")
    return path


def test_the_wilson_bound_passes_26_of_30_and_fails_25_of_30():
    assert ig.wilson_lower(26, 30) == pytest.approx(0.703, abs=0.001)
    assert ig.wilson_lower(25, 30) == pytest.approx(0.664, abs=0.001)
    assert ig.gate(26, 30)["passed"] and not ig.gate(25, 30)["passed"]


def test_fewer_than_30_labelled_faces_fail_even_when_all_agree():
    said = ig.gate(29, 29)
    assert not said["passed"] and said["state"] == ig.FAILED
    assert ig.gate(0, 0) == {"agree": 0, "n": 0, "lower": 0.0, "passed": False, "state": ig.FAILED,
                             "min_n": 30, "min_lower": 0.7}


def test_labels_are_the_owner_field_only_and_an_empty_one_is_no_label():
    doc = label_doc(["good", "", "bad", "maybe"])
    assert ig.owner_labels(doc) == {"faces_x/c00.png": "good", "faces_x/c02.png": "bad"}


def test_the_eye_judge_never_supplies_a_label(tmp_path):
    """Every crop's `eye` says clear and no owner wrote anything: nothing is labelled."""
    doc = label_doc([""] * 30, ["clear"] * 30)
    assert ig.owner_labels(doc) == {}
    assert ig.calibrate([write_labels(tmp_path, doc)], {"eye_judge": ig.eye_judge_reads})["eye_judge"]["n"] == 0


def test_a_label_file_not_named_face_labels_under_review_is_refused(tmp_path):
    path = tmp_path / "eye_verdict.json"
    path.write_text(json.dumps(label_doc(["good"] * 30)), encoding="utf-8")
    with pytest.raises(ValueError, match="face_labels"):
        ig.read_labels([path])


def test_the_eye_judge_is_measured_against_the_owner_as_a_candidate(tmp_path):
    owner = ["good"] * 27 + ["bad"] * 3
    eye = ["clear"] * 30
    said = ig.calibrate([write_labels(tmp_path, label_doc(owner, eye))], {"eye_judge": ig.eye_judge_reads})
    assert said["eye_judge"]["agree"] == 27 and said["eye_judge"]["n"] == 30 and said["eye_judge"]["passed"]


def test_the_cel_instrument_reads_good_above_its_own_zero_line():
    assert ig.cel_word(0.0) == "bad" and ig.cel_word(12.5) == "good" and ig.cel_word(None) is None


def test_below_the_gate_every_eye_cel_row_prints_instrument_failed():
    rows = [{"take": "T05", "eye_cel_replay": 81.7}, {"take": "T06", "eye_cel_replay": None}]
    out = ig.stamp(rows, ig.gate(3, 4))
    assert all(r["instrument_state"] == ig.FAILED for r in out)
    assert out[0]["eye_cel_replay"] == 81.7          # the number is kept, its standing is not


def test_the_proof_row_has_the_design_5_schema():
    row = ig.proof_row("instrument_gate.eye_cel", "Q1", False, 0, 0, ["review/face_labels_0db3d8d9.json"],
                       [], "face_eye.cel", ig.FAILED, "compliance")
    assert set(row) == {"check", "question", "passed", "n_points", "n_distinct", "evidence", "match_classes",
                        "instrument", "instrument_state", "kind"}
    with pytest.raises(ValueError):
        ig.proof_row("x", "Q1", True, 1, 1, [], [], "", "", "opinion")
