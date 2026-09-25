"""The identity observe, armed.  A take is bound to a cast sheet; every readable
face is embedded and scored against the bank, and `identity_gate.judge` says
MATCH, STRANGER or DRIFT from the vectors alone.  `detect=` and `embed=` are
injected: no frame is decoded and no model is loaded."""
from pathlib import Path

import numpy as np

from studio import identity_gate as g
from studio.measure import faces

FIX = Path(__file__).parent / "fixtures" / "measures"
BANK = np.load(FIX / "faces_bank.npy")          # sheet_a, sheet_b, f0, f1, f2, stranger, slipped
FRAME = np.zeros((100, 100, 3), dtype=np.uint8)
BOX = [30, 20, 70, 60]                             # 40 px tall on 100: h 0.4, readable
FRONTAL = [[38, 32], [62, 32], [50, 44], [40, 54], [60, 54]]


def _detect(_frame):
    return [{"box": BOX, "landmarks": FRONTAL}]


def _embed_from(vectors):
    it = iter(vectors)
    return lambda _frame, _box: next(it)


def _bank():
    return {"a": [BANK[0]], "b": [BANK[1]]}


def test_a_take_uses_the_style_it_was_bound_to():
    seen = faces.observe([FRAME] * 3, [0], _bank(), _detect, _embed_from(BANK[2:5]))
    verdict = g.judge(seen, expected=["a"], refs=["char-a.png"])
    assert verdict.ok and verdict.present == {"a": 3}
    assert all(f.best == "a" and f.cos >= g.MATCH for f in seen)


def test_a_stranger_in_the_take_is_hard_and_armed():
    seen = faces.observe([FRAME] * 2, [0], _bank(), _detect, _embed_from([BANK[2], BANK[5]]))
    verdict = g.judge(seen, expected=["a"], refs=["char-a.png"])
    assert g.ARMED is True
    assert verdict.hard and verdict.hard[0].startswith("STRANGER frame 1")


def test_a_slip_inside_a_segment_is_drift():
    seen = faces.observe([FRAME] * 2, [0], _bank(), _detect, _embed_from([BANK[2], BANK[6]]))
    verdict = g.judge(seen, expected=["a"], refs=["char-a.png"])
    assert any(h.startswith("DRIFT a") for h in verdict.hard)


def test_identity_dq_fails_the_take_on_a_hard_finding(monkeypatch):
    monkeypatch.setattr(g, "_backend", lambda: object())
    monkeypatch.delenv(g.SWITCH, raising=False)
    report = g.identity_dq([FRAME] * 2, [0], ["a"], ["char-a.png"], sheets={"a": Path("char-a.png")},
                           detect=_detect, embed=_embed_from([BANK[2], BANK[5]]),
                           bank=_bank())
    assert report["measured"] and not report["ok"] and report["hard"]


def test_the_yaw_is_the_nose_off_the_eye_line():
    assert faces.yaw(FRONTAL) == 0.0
    assert faces.yaw([[38, 32], [62, 32], [70, 44], [40, 54], [60, 54]]) > g.FRONTAL
