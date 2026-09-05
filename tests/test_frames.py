"""Frame sampling for a take: stills read by the vision model, none inside
the head leak where H3 shows the reference sheet itself."""
from __future__ import annotations

from pathlib import Path

from studio import frames


class TestFrameTimes:
    def test_samples_avoid_the_reference_leak_at_the_head(self):
        times = frames.frame_times(7.0, count=3, head=1.0)
        assert times[0] >= 1.0 and times[-1] < 7.0 and len(times) == 3

    def test_the_default_head_is_the_measured_leak(self):
        assert frames.HEAD_LEAK_SECONDS == 1.0
        assert frames.frame_times(7.0)[0] > frames.HEAD_LEAK_SECONDS

    def test_a_take_shorter_than_the_leak_still_yields_frames(self):
        times = frames.frame_times(0.5, count=2, head=1.0)
        assert len(times) == 2 and all(t >= 1.0 for t in times)


class TestFrameAt:
    def test_asks_ffmpeg_for_one_frame_at_the_time(self, monkeypatch, tmp_path):
        calls: list[list[str]] = []
        monkeypatch.setattr(frames.subprocess, "run", lambda cmd, check: calls.append(cmd))
        dest = frames.frame_at(Path("take.mp4"), 2.5, tmp_path / "2.50.png")
        assert dest == tmp_path / "2.50.png"
        assert calls[0][calls[0].index("-ss") + 1] == "2.500" and "-frames:v" in calls[0]
