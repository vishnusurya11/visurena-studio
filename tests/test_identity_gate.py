"""G4.7 -- the identity gate.  No model, no file, no credit: the faces are
hand-built observations at the calibrated numbers from review8/identity.md.
The measuring half (MTCNN + VGGFace2) is behind a feature flag; with the
library absent the gate reports 'not measured' and fails nothing.
"""
from __future__ import annotations

import numpy as np

from studio import identity_gate as g


def vec(seed: int) -> np.ndarray:
    v = np.random.default_rng(seed).normal(size=512)
    return v / np.linalg.norm(v)


def face(k, h, watson, holmes, stamford, v=None, yaw=0.0, seg=0):
    return g.Face(k=k, h=h, scores={"john_watson": watson, "sherlock_holmes": holmes, "stamford": stamford},
                  vec=v, yaw=yaw, seg=seg)


def test_the_thresholds_are_the_measured_populations():
    """review8/identity.md: the right man scores 0.61-0.94, strangers 0.43/0.21/
    0.03/-0.04 (MATCH 0.60, STRANGER 0.45); in-segment drift is >= 0.81 on every
    real ep01 pair against 0.72 for the one true slip (iteration 3 T09).

    RECALIBRATED on episode 10 (docs/calibration/identity.md, dq10/A): READABLE
    0.12 -> 0.15, because T06's 0.12-0.13 faces are the only frontal faces that
    score under 0.60 for the right man; FRONTAL 0.50 -> 0.35, because T29 f5
    (yaw 0.44) and T33 f4 (yaw 0.43) are full profiles by eye and the old wall
    let them into the drift pair."""
    assert (g.READABLE, g.FRONTAL) == (0.15, 0.35)
    assert (g.MATCH, g.STRANGER, g.DRIFT) == (0.60, 0.45, 0.75)


def test_a_face_at_the_old_readable_floor_is_no_longer_judged():
    """ep10 T06: Ferrier at 0.12-0.13 of frame scored 0.56-0.60 while frontal."""
    assert g.readable([face(1, 0.13, 0.1, 0.1, 0.58)]) == []


def test_a_three_quarter_turn_is_a_profile_now():
    """ep10 T29 f5 at yaw 0.44 and T33 f4 at 0.43 are profiles by eye."""
    assert g.readable([face(5, 0.3, 0.1, 0.1, 0.47, yaw=0.44)]) == []
    assert g.readable([face(0, 0.3, 0.1, 0.1, 0.79, yaw=0.30)]) != []


def test_small_faces_are_not_judged():
    faces = [face(0, 0.05, 0.10, 0.10, 0.10)]
    assert g.readable(faces) == []
    assert g.judge(faces, ["john_watson"], ["char-john_watson.png"]).ok


def test_matching_face_is_identified():
    assert g.identify(face(0, 0.3, 0.72, 0.31, 0.12)) == "john_watson"


def test_profile_is_not_judged():
    faces = [face(3, 0.17, 0.57, 0.2, 0.1, yaw=0.92)]      # iteration 3 T09 f3: Watson in profile
    assert g.readable(faces) == []


def test_weak_match_is_advisory():
    v = g.judge([face(3, 0.29, 0.2, 0.55, 0.1)], ["sherlock_holmes"], ["char-sherlock_holmes_lab.png"])
    assert v.present == {"sherlock_holmes": 1}
    assert v.flags == ["WEAK frame 3: sherlock_holmes 0.55 < 0.6"]
    assert v.hard == []                                     # advisory: it does not fail the take


def test_drift_across_a_cut_is_not_drift():
    a, b = vec(1), vec(2)
    faces = [face(1, 0.13, 0.1, 0.1, 0.81, a, seg=0), face(4, 0.49, 0.1, 0.1, 0.75, b, seg=1)]
    assert g.drift(faces) == {}                            # iteration 4 T02: two-shot, then close


def test_stranger_below_threshold_is_hard():
    f = face(2, 0.3, 0.40, 0.43, 0.28)
    assert g.identify(f) is None
    v = g.judge([f], ["john_watson"], ["char-john_watson.png"])
    assert v.flags == ["STRANGER frame 2: best sherlock_holmes 0.43 < 0.45"]
    assert v.hard == v.flags and not v.ok


def test_uncast_face_is_flagged():
    faces = [face(2, 0.4, 0.20, 0.15, 0.71)]          # Stamford close-up
    v = g.judge(faces, expected=[], refs=["plate_criterion.png", "ref_take_02.png"])
    assert "UNCAST stamford: on screen, not in the plan's faces" in v.flags


def test_unreferenced_face_is_flagged_even_when_cast():
    faces = [face(2, 0.4, 0.20, 0.15, 0.71)]
    v = g.judge(faces, expected=["stamford"], refs=["plate_gateway.png", "ref_take_08.png"])
    assert v.flags == ["UNREFERENCED stamford: on screen, cast sheet not in refs"]


def test_referenced_cast_face_passes():
    faces = [face(0, 0.4, 0.20, 0.15, 0.71), face(4, 0.4, 0.18, 0.12, 0.69)]
    v = g.judge(faces, ["stamford"], ["char-stamford.png", "plate_gateway.png"])
    assert v.ok and v.present == {"stamford": 2}


def test_drift_between_first_and_last_frame_is_hard():
    a, b = vec(1), vec(2)                       # unrelated vectors: cosine ~ 0
    faces = [face(0, 0.4, 0.70, 0.3, 0.1, a), face(4, 0.4, 0.62, 0.3, 0.1, b)]
    v = g.judge(faces, ["john_watson"], ["char-john_watson.png"])
    assert any(f.startswith("DRIFT john_watson") for f in v.hard)


def test_no_drift_when_same_vector():
    a = vec(3)
    faces = [face(0, 0.4, 0.70, 0.3, 0.1, a), face(4, 0.4, 0.66, 0.3, 0.1, a)]
    assert g.drift(faces) == {"john_watson": 1.0}
    assert g.judge(faces, ["john_watson"], ["char-john_watson.png"]).ok


def test_drift_needs_two_frames():
    assert g.drift([face(0, 0.4, 0.70, 0.3, 0.1, vec(4))]) == {}


def swing(seed: int, amount: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """One man in three poses: the base vector pushed one way, then the other,
    by `amount` along a direction orthogonal to it."""
    b, u = vec(seed), vec(seed + 100)
    u = u - (u @ b) * b
    u /= np.linalg.norm(u)
    first, last = b + amount * u, b - amount * u
    return first / np.linalg.norm(first), b, last / np.linalg.norm(last)


def test_a_pose_swing_over_three_frames_is_not_drift():
    """ep10: same-person first-vs-last pairs measured 0.60-0.69 whenever the
    head was pitched or turned, while every frame against the segment's MEDIAN
    embedding measured 0.82-0.98.  With three or more readable frames the
    drift is the minimum cosine to the median, not the first-last pair."""
    first, mid, last = swing(7, 0.6)
    assert float(first @ last) < g.DRIFT                      # the pair alone would have failed it
    faces = [face(0, 0.4, 0.70, 0.3, 0.1, first), face(2, 0.4, 0.72, 0.3, 0.1, mid),
             face(4, 0.4, 0.71, 0.3, 0.1, last)]
    assert g.drift(faces)["john_watson"] >= g.DRIFT
    assert g.judge(faces, ["john_watson"], ["char-john_watson.png"]).ok


def test_a_real_slip_in_a_run_of_three_is_still_drift():
    """Two frames of one man and a third of another: the third against the
    median of the run reads as a stranger's cosine."""
    a, c = vec(1), vec(2)
    faces = [face(0, 0.4, 0.70, 0.3, 0.1, a), face(2, 0.4, 0.70, 0.3, 0.1, a), face(4, 0.4, 0.62, 0.3, 0.1, c)]
    assert g.drift(faces)["john_watson"] < g.DRIFT


def test_two_frames_still_compare_first_with_last():
    """ep01's one true slip (iteration 3 T09) had two readable frames at 0.72."""
    first, _, last = swing(8, 0.45)
    faces = [face(0, 0.4, 0.70, 0.3, 0.1, first), face(4, 0.4, 0.66, 0.3, 0.1, last)]
    assert g.drift(faces)["john_watson"] == round(float(first @ last), 3)


def test_the_median_embedding_is_a_unit_vector():
    first, mid, last = swing(9, 0.6)
    assert abs(float(np.linalg.norm(g.median_embedding([first, mid, last]))) - 1.0) < 1e-6


# the feature flag -------------------------------------------------------------

def test_the_gate_is_off_without_the_face_model(monkeypatch):
    """facenet-pytorch is not in the venv (checked 2026-09-11).  The gate must say
    so and fail nothing, rather than crash the DQ of every take."""
    monkeypatch.setattr(g, "_backend", lambda: None)
    assert not g.enabled()
    report = g.identity_dq(None, [], [], [])
    assert report == {"measured": False, "ok": True, "note": "not measured: face model not installed",
                      "flags": [], "hard": [], "present": {}}


def test_an_explicit_off_switch_disables_a_working_backend(monkeypatch):
    """A WORKING backend means one that can also MEASURE.

    This used to supply only `_backend` and assert that "on" armed the gate --
    which was true, and was the fault: `observe` raises NotImplementedError, so
    arming it crashed the DQ of every take. `enabled()` now requires a measurer
    too, so this test supplies one; it is testing the SWITCH, and the switch
    still wins over a gate that could otherwise run.
    See tests/test_the_identity_switch_cannot_arm_a_gate_that_raises.py."""
    monkeypatch.setattr(g, "_backend", lambda: object())
    monkeypatch.setattr(g, "observe", lambda video, segments, sheets, samples=8: [])
    monkeypatch.setenv(g.SWITCH, "off")
    assert not g.enabled()
    monkeypatch.setenv(g.SWITCH, "on")
    assert g.enabled()


def test_a_measured_verdict_carries_the_flags_and_stays_advisory(monkeypatch):
    """ARMED is False for one episode: on ep10 every hard flag the calibrated
    gate raised was pose (four same-person takes), and its only true positives
    are two ep01 takes.  The finding is kept, in `flags`, and fails nothing."""
    faces = [face(2, 0.3, 0.40, 0.43, 0.28)]
    monkeypatch.setattr(g, "_backend", lambda: object())
    monkeypatch.setattr(g, "observe", lambda *args, **kw: faces)
    report = g.identity_dq("T09.mp4", [], ["john_watson"], ["char-john_watson.png"])
    assert report["measured"] and report["ok"]
    assert report["hard"] == [] and not g.ARMED
    assert report["flags"] == ["STRANGER frame 2: best sherlock_holmes 0.43 < 0.45"]
    assert "advisory" in report["note"]


def test_arming_the_gate_makes_the_same_finding_hard(monkeypatch):
    faces = [face(2, 0.3, 0.40, 0.43, 0.28)]
    monkeypatch.setattr(g, "_backend", lambda: object())
    monkeypatch.setattr(g, "observe", lambda *args, **kw: faces)
    monkeypatch.setattr(g, "ARMED", True)
    report = g.identity_dq("T09.mp4", [], ["john_watson"], ["char-john_watson.png"])
    assert not report["ok"] and report["hard"] == ["STRANGER frame 2: best sherlock_holmes 0.43 < 0.45"]


def test_observe_is_still_the_placeholder_without_facenet():
    """The venv has OpenCV's YuNet (boxes and landmarks; studio/face_end.py)
    and not facenet-pytorch (embeddings), so the measurer stays unwritten and
    the gate stays honestly 'not measured'."""
    import pytest
    with pytest.raises(NotImplementedError):
        g.observe(None, [], {})
