"""A weak proxy must not hard-fail a master beside an exact measurement of the
same fact.

`qc.missing_cuts` asks whether each planned cut is "seen", and seeing is
ffmpeg's `select=gt(scene,0.1)` -- a content-difference heuristic. Two shots of
the SAME ROOM at the same lens and the same light score under that and read as a
cut that never happened. `qc.verdict` then hard-fails the delivered master.

Meanwhile `edit_gate.cut_exact` has already proved the same splice frame by
frame: the frame before the cut IS the previous take's last placed frame and the
frame at it IS the next take's first, within `SAME_FRAME = 4.0` where encoder
noise measures 0.16-0.59 and another picture measures 32-63. That is not a
heuristic, it is the thing itself.

THE RISK IS LIVE, not theoretical. Episode 5 plays five of its six setups in one
room -- the 221B sitting room from five corners -- with the same gaslight and the
same fire in most of them. It is the first episode where a genuine cut between
two takes can look like no cut at all to a scene detector.

So a planned cut that the edit gate proved exact is not missing, whatever the
scene metric saw. The heuristic still speaks for cuts the edit gate could not
measure, which is every cut when the gate did not run.
"""
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("ep_qc_proven", ROOT / "scripts" / "episode" / "qc.py")
qc = importlib.util.module_from_spec(_spec)
sys.modules["ep_qc_proven"] = qc
_spec.loader.exec_module(qc)

GOOD = {"lufs_ok": True, "tp_ok": True, "lines": [{"passed": True}],
        "edit": {"ok": True, "measured": True}}


def test_a_cut_the_scene_metric_saw_is_present():
    assert qc.missing_cuts([4.0], [4.05]) == []


def test_a_cut_nothing_saw_is_missing():
    assert qc.missing_cuts([4.0], [9.0]) == [4.0]


def test_a_cut_proved_exact_is_not_missing():
    """The same room from two corners: the scene metric sees nothing."""
    proven = [{"at": 96, "exact": True}]          # frame 96 at 24 fps = 4.0 s
    assert qc.missing_cuts([4.0], [], proven=proven) == []


def test_a_cut_the_edit_gate_measured_and_refused_is_still_missing():
    proven = [{"at": 96, "exact": False}]
    assert qc.missing_cuts([4.0], [], proven=proven) == [4.0]


def test_the_proof_is_matched_within_the_same_tolerance():
    """96 frames is 4.0 s; a proof 0.05 s away still answers for this cut."""
    assert qc.missing_cuts([4.05], [], proven=[{"at": 96, "exact": True}]) == []


def test_a_proof_somewhere_else_answers_for_nothing():
    assert qc.missing_cuts([4.0], [], proven=[{"at": 240, "exact": True}]) == [4.0]


def test_no_proof_leaves_the_heuristic_in_charge():
    assert qc.missing_cuts([4.0], []) == [4.0]
    assert qc.missing_cuts([4.0], [], proven=[]) == [4.0]


def test_the_verdict_passes_a_master_whose_cuts_were_all_proved():
    report = dict(GOOD, missing_cuts=[], internal_cuts=[])
    assert qc.verdict(report) is True
