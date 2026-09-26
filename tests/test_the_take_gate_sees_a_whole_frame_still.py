"""The take gate reads WHOLE-FRAME stillness (root cause 2026-09-26, D12).

`motion_gate` called a frame alive when its busiest 24x24 block moved, so every
ep12 take read 0 % frozen while five were 70-100 % static by optical flow.
`studio.stillness` (fitted on 290 takes: the five owner-dead ep12 takes fail,
the 28 known-good pass) is a HARD row, `frozen-whole`, which the take ladder
treats as a frozen fault; a shot the plan declares `still` is exempt."""
from __future__ import annotations

from studio import stillness, take_ladder, take_verdict as tv
from studio.judges import take_eye


def fake_measure(share):
    def measure(video, seconds=None, start=0.0, exempt=False):
        still = share >= stillness.WALL and (seconds or 0) >= stillness.MIN_SECONDS and not exempt
        return {"static_share": share, "still": still, "advisory": False, "exempt": exempt,
                "longest_static_run_s": 5.0, "seconds": seconds, "camera_share": 0.0,
                "subject_share": 0.0, "mean_flow": 0.05}
    return measure


def test_a_whole_frame_still_is_a_hard_failing_row(monkeypatch):
    monkeypatch.setattr(stillness, "measure", fake_measure(0.95))
    row = tv.stillness_row("T14.mp4", 8.0, {})
    assert row.name == "frozen-whole" and row.hard and not row.ok


def test_a_declared_still_is_exempt(monkeypatch):
    monkeypatch.setattr(stillness, "measure", fake_measure(0.95))
    assert tv.stillness_row("T14.mp4", 8.0, {"still": True}).ok


def test_the_ladder_treats_it_as_frozen():
    assert "frozen-whole" in take_ladder.FROZEN and take_ladder.CAUSE_OF["frozen-whole"] == "frozen"
    assert "frozen-whole" in take_eye.GEOMETRY
