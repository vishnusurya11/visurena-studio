"""The av3 pace guard (Jekyll ep01 2026-10-18): the upscale cap is a PER-PASS pace budget.
After 600 frames the pass is projected from a rolling fps window against the cap row (15 min);
only a pass projected past cap + 25 % is cut (exit 76, fallback to rtx4x); a pass that fits is
never cut.  A failure names its frame and shot.  Fake clocks and models, $0."""
from __future__ import annotations

import subprocess

import pytest

from studio import master_av3 as av
from studio import master_upscale as mu

CAP = 900.0


class Clock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


def run_pace(total: int, seconds_per_frame: float, frames: int = 700):
    """Drive a Pace with a fake clock; the exception it raised, or None."""
    clock = Clock()
    pace = av.Pace(total, CAP, clock=clock)
    try:
        for n in range(1, frames + 1):
            clock.now += seconds_per_frame
            pace.frame(n)
    except av.TooSlow as slow:
        return slow
    return None


def test_a_pass_projected_at_20_minutes_is_cut_as_too_slow():
    got = run_pace(3348, 1200.0 / 3348)
    assert isinstance(got, av.TooSlow) and "1200" in str(got).replace(".0", "")


def test_a_pass_projected_at_13_minutes_is_never_cut():
    assert run_pace(3348, 780.0 / 3348, frames=3348) is None


def test_a_pass_projected_inside_cap_plus_25_percent_is_never_cut():
    assert run_pace(3348, 1100.0 / 3348, frames=3348) is None


def test_nothing_is_decided_before_600_frames():
    assert run_pace(3348, 5.0, frames=599) is None


def test_the_projection_follows_the_recent_window_not_the_start():
    clock = Clock()
    pace = av.Pace(3348, CAP, clock=clock)
    for n in range(1, 601):       # a slow cold start, as the model loads
        clock.now += 0.25
        pace.frame(n)
    for n in range(601, 1301):    # then fast: 40 fps
        clock.now += 0.025
        pace.frame(n)
    assert pace.projected(1300) < CAP


def test_a_progress_line_every_300_frames(capsys):
    clock = Clock()
    pace = av.Pace(3348, CAP, clock=clock)
    for n in range(1, 901):
        clock.now += 0.1
        pace.frame(n)
    lines = [l for l in capsys.readouterr().err.splitlines() if l.startswith("av3 ")]
    assert [l.split()[1] for l in lines] == ["300/3348", "600/3348", "900/3348"]
    assert all("fps" in l and "eta" in l for l in lines)


def test_a_too_slow_worker_exits_with_its_own_code(monkeypatch, capsys):
    def slow(job, hard_exit=None):
        raise av.TooSlow("projected 1200 s against 900 s")
    monkeypatch.setattr(av, "run", slow)
    monkeypatch.setattr(av.Path, "read_text", lambda self, encoding=None: "{}")
    with pytest.raises(SystemExit) as out:
        av.main(["master_av3.py", "job.json"])
    assert out.value.code == av.SLOW == 76


def test_the_fallback_says_too_slow(tmp_path, monkeypatch, capsys):
    from contextlib import nullcontext
    calls = []
    monkeypatch.setattr(mu, "av3_paths", lambda env=None: (tmp_path / "py.exe", tmp_path / "w.pth"))
    monkeypatch.setattr(mu, "run_worker", lambda python, job: mu.AV3_SLOW)
    monkeypatch.setattr(mu, "rtx_missing", lambda: "")
    monkeypatch.setattr("studio.compute_device.claim", lambda job, root=None: nullcontext())
    monkeypatch.setattr(mu, "master", lambda *a, **k: calls.append(a) or a[1])
    mu.av3_master(tmp_path / "l.txt", tmp_path / "o.mp4", 768, 768, mu.CHOICES["av3"], 24, None, None, [5], "cuda")
    assert "CAP upscale: av3 too slow, fell back to rtx4x" in capsys.readouterr().err
    assert calls[0][4] == mu.CHOICES["rtx4x"]


def test_the_cap_rides_the_job(tmp_path):
    job = mu.av3_job(tmp_path / "l", tmp_path / "o", 768, 768, mu.CHOICES["av3"], 24, [], [], tmp_path / "w", "cpu",
                     cap_s=900.0)
    assert job["cap_s"] == 900.0


def test_a_failed_pass_names_its_frame(tmp_path, capsys):
    side = 32
    clip = tmp_path / "p.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"testsrc=s={side}x{side}:r=24:d=10",
                    "-f", "lavfi", "-t", "10", "-i", "sine=f=440:r=48000", "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", str(clip)], check=True)
    listing = tmp_path / "l.txt"
    listing.write_text(f"file '{clip.as_posix()}'\n", encoding="utf-8")
    seen = {"k": 0}

    def up(frame):
        seen["k"] += 1
        if seen["k"] == 130:
            raise RuntimeError("CUDA error")
        return frame
    with pytest.raises(RuntimeError):
        av.streamed(listing, tmp_path / "o.mp4", side, side, 1, 24, up, [100, 200], expected_frames=240)
    assert "CAP upscale: av3 failed at frame 129/240 (shot 2)" in capsys.readouterr().err


def test_the_shot_of_a_frame_counts_the_cuts_before_it():
    assert [av.shot_of(n, [100, 200]) for n in (0, 99, 100, 199, 200, 500)] == [1, 1, 2, 2, 3, 3]
