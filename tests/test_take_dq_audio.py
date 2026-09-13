"""Only a dialogue take is gated on audio lag: a narration take carries silence."""
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("take_dq", Path(__file__).resolve().parents[1] / "scripts" / "episode" / "take_dq.py")
dq = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dq)


def test_a_silent_narration_take_is_not_gated_on_lag():
    assert dq.lag_verdict(None, dialogue=False) == {"lag_s": 0.0, "lag_ok": True, "lag_measured": False}


def test_a_dialogue_take_is_gated_on_lag():
    assert dq.lag_verdict(0.010, dialogue=True)["lag_ok"]
    assert not dq.lag_verdict(-7.28, dialogue=True)["lag_ok"]


def test_end_pins_belong_to_their_segment_when_judging_the_beat():
    """Iteration 4: anchors carry END pins (Q14_0 again at frame 117, Q14_1E at 237);
    a frame matching the start cell while the END pin is 'expected' is on the beat."""
    anchors = [("Q14_0.png", 0), ("Q14_1.png", 121), ("Q14_2.png", 181), ("Q14_0.png", 117), ("Q14_1E.png", 177)]
    order = dq.segment_order(anchors)
    assert order == ["Q14_0.png", "Q14_1.png", "Q14_2.png"]
    assert dq.expected_anchor(anchors, at=5.0) == 3          # frame 120: the latest pin is Q14_0's END pin at 117
    assert dq.expected_anchor(anchors, at=5.1) == 1          # frame 122: Q14_1 began at 121
    assert dq.segment_of(anchors, 3, order) == 0 and dq.segment_of(anchors, 4, order) == 1
