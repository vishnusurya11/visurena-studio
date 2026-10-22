"""The voice ear hears every clip at 16 kHz, the rate ECAPA was trained on.

MEASURED 2026-10-21 (docs/audit/2026-10-21_voice_bench, VERDICT row 9): `embedding`
and `self_similarity` read the file with `sf.read` and handed ECAPA its 24 kHz
samples untouched.  The model's Fbank keeps its 16 kHz default, so every voice was
heard 1.5x slow and low: on Jekyll ep01's shipped lines a wrong character cleared the
floor in 70 of 152 trials, against 3 of 152 resampled.  `mono_16k` sat unused in the
same module.  Every clip now goes through it.

The fixtures are Jekyll ep01's own lines and cast designs, trimmed (tests/fixtures/voice).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from studio import voice_ear

VOICE = Path(__file__).resolve().parent / "fixtures" / "voice"


def tone(path: Path, rate: int, seconds: float) -> Path:
    t = np.arange(int(rate * seconds)) / rate
    sf.write(str(path), (0.2 * np.sin(2 * np.pi * 150.0 * t)).astype("float32"), rate)
    return path


def counting(seen: list):
    """A fake ECAPA that records how many samples it was handed."""
    def embed(samples, device=""):
        seen.append(len(samples))
        return np.array([1.0, 0.0])
    return embed


def test_a_24k_file_reaches_the_encoder_at_16k(tmp_path, monkeypatch):
    seen = []
    monkeypatch.setattr(voice_ear, "embed_samples", counting(seen))
    voice_ear.embedding(tone(tmp_path / "a.wav", 24000, 1.0), device="cpu")
    assert seen == [16000]


def test_a_16k_file_reaches_the_encoder_unchanged(tmp_path, monkeypatch):
    seen = []
    monkeypatch.setattr(voice_ear, "embed_samples", counting(seen))
    voice_ear.embedding(tone(tmp_path / "b.wav", 16000, 1.0), device="cpu")
    assert seen == [16000]


def test_self_similarity_splits_the_16k_clip(tmp_path, monkeypatch):
    seen = []
    monkeypatch.setattr(voice_ear, "embed_samples", counting(seen))
    voice_ear.self_similarity(tone(tmp_path / "c.wav", 24000, 2.0), device="cpu")
    assert seen == [16000, 16000]


def test_the_docstring_cites_the_model_cards_eer():
    """The model README (lines 37-39) gives 0.80 % on VoxCeleb1, not 0.73 %."""
    assert "0.80%" in voice_ear.__doc__ and "0.73%" not in voice_ear.__doc__


def cosine(a, b) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


@pytest.mark.local
def test_a_24k_clip_and_its_16k_resample_are_one_embedding(tmp_path):
    from scipy.signal import resample_poly

    wave, rate = sf.read(str(VOICE / "narrator_l02.wav"), dtype="float32")
    assert rate == 24000
    sf.write(str(tmp_path / "l02_16k.wav"), resample_poly(wave, 2, 3).astype("float32"), 16000)
    native = voice_ear.embedding(VOICE / "narrator_l02.wav", device="cpu")
    resampled = voice_ear.embedding(tmp_path / "l02_16k.wav", device="cpu")
    assert cosine(native, resampled) > 0.99


@pytest.mark.local
def test_a_wrong_voice_sits_well_under_the_genuine_one():
    """The narrator's line against Utterson's design: 0.669 vs 0.722 at 24 kHz (0.05
    apart), 0.33 vs 0.81 at 16 kHz.  A wrong voice must sit the cast margin under."""
    line = VOICE / "narrator_l02.wav"
    genuine = voice_ear.similarity(line, VOICE / "narrator_design.wav", device="cpu")
    wrong = voice_ear.similarity(line, VOICE / "utterson_design.wav", device="cpu")
    assert genuine - wrong >= 0.08
