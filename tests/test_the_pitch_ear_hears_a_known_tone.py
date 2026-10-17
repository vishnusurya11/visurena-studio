"""`voice_ear.pitch` reads F0 with torchcrepe (2026-10-16 battery part 2: the
import failed in the repo env, so G1 fell back to librosa pYIN). The package is
pinned in the `voice` group; a known tone must read back as itself."""
from __future__ import annotations

import importlib.util
import math
import wave
from pathlib import Path

import numpy as np

from studio import voice_ear


def tone(path: Path, hz: float, seconds: float = 0.6, rate: int = 16000) -> Path:
    t = np.arange(int(seconds * rate)) / rate
    samples = (0.4 * np.sin(2 * math.pi * hz * t) * 32767).astype("<i2")
    with wave.open(str(path), "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(rate)
        out.writeframes(samples.tobytes())
    return path


def test_torchcrepe_is_installed_with_the_voice_group():
    assert importlib.util.find_spec("torchcrepe") is not None


def test_the_clip_loads_as_one_16k_channel_without_torchcodec(tmp_path):
    """torchaudio 2.11's load needs torchcodec, which the env does not carry:
    the ear reads the file through soundfile and resamples itself."""
    wave_ = voice_ear.mono_16k(tone(tmp_path / "b.wav", 150.0, seconds=0.5, rate=44100))
    assert tuple(wave_.shape) == (1, 8000)


def test_a_220_hz_tone_reads_as_220_hz(tmp_path):
    got = voice_ear.pitch(tone(tmp_path / "a3.wav", 220.0), device="cpu")
    assert abs(got - 220.0) / 220.0 < 0.03, got


def test_a_44_1_khz_file_is_resampled_before_reading(tmp_path):
    got = voice_ear.pitch(tone(tmp_path / "a3_44k.wav", 150.0, rate=44100), device="cpu")
    assert abs(got - 150.0) / 150.0 < 0.03, got
