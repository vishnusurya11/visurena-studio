"""Integrated loudness and true peak come from one loudnorm pass over a file, audio only
(`-vn`); a second ask of the same bytes reads the cached run.  $0, ffmpeg faked."""
from __future__ import annotations

import os

from studio import trailer_assemble as ta


def counting(monkeypatch):
    calls = []
    monkeypatch.setattr(ta, "_measure_loudness", lambda argv: calls.append(argv) or {"input_i": "-16.0", "input_tp": "-2.1"})
    ta._loudnorm_cache.clear()
    return calls


def test_integrated_and_true_peak_run_ffmpeg_once(tmp_path, monkeypatch):
    calls = counting(monkeypatch)
    master = tmp_path / "m.mp4"
    master.write_bytes(b"x")
    assert (ta.integrated(master), ta.true_peak(master)) == (-16.0, -2.1)
    assert len(calls) == 1 and "-vn" in calls[0]


def test_a_changed_file_is_measured_again(tmp_path, monkeypatch):
    calls = counting(monkeypatch)
    master = tmp_path / "m.mp4"
    master.write_bytes(b"x")
    ta.integrated(master)
    master.write_bytes(b"xy")
    os.utime(master, (1, 1))
    ta.integrated(master)
    assert len(calls) == 2
