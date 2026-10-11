"""The bench's room-tone guide arm (C1_verdict #8; bench block 4).

H3 continues the line into the guide's digitally silent tail, and every guide we
ever rendered padded the line with `anullsrc` -- exact zero, -120 dB, a value the
model itself never writes (its quiet tails are -55 to -95 dB). The arm fills the
pad AFTER the line with seeded brown noise at -50 dBFS; the line's own samples and
the guide's length do not change, and the arm says which tail it ran (`knobs()`
reports `guide_tail`), so a fix that changes nothing cannot pass for one.
Production `composite()` is untouched.
"""
from __future__ import annotations

import numpy as np
import soundfile as sf

from scripts.bench import guide_tail, h3_arms

SR = 24000


def guide(tmp_path, subtype="PCM_16"):
    t = np.arange(int(1.0 * SR)) / SR
    line = 0.3 * np.sin(2 * np.pi * 220 * t)
    sig = np.concatenate([np.zeros(int(0.25 * SR)), line, np.zeros(int(2.0 * SR))])
    path = tmp_path / "voice_04_abcd1234.wav"
    sf.write(str(path), sig, SR, subtype=subtype)
    return path


def test_the_pad_after_the_line_is_room_tone_at_minus_50_dbfs(tmp_path):
    src = guide(tmp_path)
    out = guide_tail.roomtone(src, tmp_path / "out.wav", seed=1)
    before, _ = sf.read(str(src), dtype="int16")
    after, sr = sf.read(str(out), dtype="int16")
    end = guide_tail.line_end(before)
    pad = after[end:].astype(np.float64) / 32768.0
    level = 20 * np.log10(np.sqrt(np.mean(pad ** 2)))
    assert -51.0 <= level <= -49.0
    assert sr == SR and len(after) == len(before)
    assert after[:end].tobytes() == before[:end].tobytes()


def test_the_noise_is_seeded(tmp_path):
    src = guide(tmp_path)
    a = sf.read(str(guide_tail.roomtone(src, tmp_path / "a.wav", seed=7)), dtype="int16")[0]
    b = sf.read(str(guide_tail.roomtone(src, tmp_path / "b.wav", seed=7)), dtype="int16")[0]
    assert a.tobytes() == b.tobytes()


def graph(audio: str) -> dict:
    return {"1": {"class_type": "UNETLoader", "inputs": {"unet_name": "u"}},
            "4": {"class_type": "ModelSamplingSD3", "inputs": {"model": ["1", 0]}},
            "9": {"class_type": "SaveVideo", "inputs": {}},
            "10": {"class_type": "MiniMaxH3ReferenceToVideo", "inputs": {"length": 97}},
            "11": {"class_type": "RandomNoise", "inputs": {"noise_seed": 1}},
            "20": {"class_type": "LoadAudio", "inputs": {"audio": audio}}}


def test_knobs_report_which_tail_the_arm_ran():
    assert h3_arms.knobs(graph("voice_21_764f9f44.wav"))["guide_tail"] == "zero"
    assert h3_arms.knobs(graph("voice_21_764f9f44_roomtone_0f0f0f0f.wav"))["guide_tail"] == "roomtone"


def test_a_job_asking_for_room_tone_restages_the_guide(tmp_path, monkeypatch):
    src = guide(tmp_path)
    monkeypatch.setattr(h3_arms, "comfy_input", lambda name: src)
    monkeypatch.setattr(h3_arms, "stage", lambda path: f"{__import__('pathlib').Path(path).stem}_00000000.wav")
    g = h3_arms.with_guide_tail(graph("voice_04_abcd1234.wav"), "roomtone", seed=3, work=tmp_path)
    assert h3_arms.knobs(g)["guide_tail"] == "roomtone"
    assert h3_arms.with_guide_tail(graph("voice_04_abcd1234.wav"), "zero", seed=3, work=tmp_path) == graph("voice_04_abcd1234.wav")
