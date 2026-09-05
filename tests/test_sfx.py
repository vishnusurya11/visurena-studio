"""The designed layer: synthesised, and MEASURED rather than assumed.

Real local ffmpeg on tiny synthetic renders -- nothing here is generated, so
nothing here costs anything.  Every assertion reads the rendered file back
through ebur128 or astats, because the whole reason this module exists is
that the generated versions of these cues measured nothing like their prompt.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from studio import sfx
from studio.trailer_assemble import clip_seconds, integrated


def band_rms(path: Path, start: float, seconds: float) -> float:
    """RMS in dB over one slice of a rendered cue."""
    result = subprocess.run(
        ["ffmpeg", "-v", "info", "-nostats", "-ss", f"{start:.3f}", "-t", f"{seconds:.3f}",
         "-i", str(path), "-af", "astats=measure_perchannel=none", "-f", "null", "-"],
        capture_output=True, text=True, errors="replace")
    for line in result.stderr.splitlines():
        if "RMS level dB" in line:
            return float(line.split(":")[-1])
    raise AssertionError("astats reported no RMS level")


class TestRoomTone:
    """Rule E: atmos wherever the music drops out, so the drop-out is
    DESIGNED.  Run 10's pre-title gap was digital silence -- a dropped
    stream, not a held breath."""

    def test_it_lands_near_the_atmos_level_the_rule_asks_for(self, tmp_path):
        tone = sfx.room_tone(tmp_path / "room.wav", seconds=4.0)
        assert integrated(tone) == pytest.approx(sfx.ROOM_TONE_LUFS, abs=2.0)

    def test_it_is_exactly_as_long_as_the_silence_it_fills(self, tmp_path):
        tone = sfx.room_tone(tmp_path / "room.wav", seconds=2.5)
        assert clip_seconds(tone) == pytest.approx(2.5, abs=0.05)

    def test_a_louder_atmos_is_asked_for_in_LUFS_not_in_gain(self, tmp_path):
        louder = sfx.room_tone(tmp_path / "loud.wav", seconds=4.0, level_lufs=-35.0)
        assert integrated(louder) == pytest.approx(-35.0, abs=2.0)


class TestRiser:
    """`sfx.riser` existed through eleven runs and was never called once."""

    def test_it_peaks_in_its_last_half_second(self, tmp_path):
        made = sfx.riser(tmp_path / "riser.wav", seconds=2.5)
        assert band_rms(made, 2.0, 0.5) - band_rms(made, 0.0, 0.5) >= 12.0

    def test_it_is_long_enough_to_be_heard_as_a_rise(self, tmp_path):
        assert clip_seconds(sfx.riser(tmp_path / "riser.wav", seconds=2.5)) == pytest.approx(2.5, abs=0.05)
