import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("respot", Path(__file__).resolve().parents[1] / "scripts" / "episode" / "respot.py")
rs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rs)


def test_cuts_scale_with_the_measured_length_and_keep_the_minimum():
    assert rs.respot([3.0, 5.5], projected=8.0, measured=10.0) == [3.75]        # 6.88 would leave 1.1 s under the projected 8.0
    assert rs.respot([3.0, 5.5], projected=8.0, measured=6.0) == [2.5]        # floor at MIN_SUB, tail too short: last cut dropped
    assert rs.respot([3.0, 5.0], projected=8.0, measured=8.0) == [3.0, 5.5]   # pushed apart to MIN_SUB


def test_the_tail_holds_under_both_the_projected_and_the_measured_length():
    """The plan validator only knows projected seconds: a cut scaled up by a
    slow reading must still leave MIN_SUB before the projected end (shot 1
    of plan_v4 crashed respot, 2026-09-11)."""
    assert rs.respot([3.0], projected=5.7, measured=7.0) == [3.2]              # 3.68 pulled back to 5.7 - 2.5
    assert rs.respot([2.6], projected=5.0, measured=8.0) == [2.5]              # pulled back to the last slot under 5.0
    assert rs.respot([3.0], projected=17 / 3, measured=6.77) == [3.16]         # floored, so 5.667 - 3.16 >= 2.5
