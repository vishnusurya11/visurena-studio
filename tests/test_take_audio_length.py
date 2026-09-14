"""A take's audio is rebuilt when the take's length changes.

`composite` returned early on `out.exists()`, and the take's audio is the
model's SHARED CLOCK -- `MiniMaxH3AddGuide` lays the audio latents on the same
t-axis as the target frames, so the audio's length is a statement about when the
picture ends.

MEASURED on episode 3, 2026-09-13: `silence_02.wav` and `silence_11.wav` are
588078 bytes = 12.25 s, written at 09:31, while T02 and T11 were re-planned and
re-rendered at 158 frames = 6.583 s that evening.  The node crops silently, so
nothing errored.

Today the stale file is only too LONG, which is harmless for silence.  The
moment a take is re-planned LONGER, the guide ends before the video does -- and
"the picture lands early" is the open fault this pipeline has been chasing all
day.  A cache keyed on a filename cannot see that; a cache keyed on the content
can.
"""
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture()
def tk(monkeypatch):
    spec = importlib.util.spec_from_file_location("tkr", ROOT / "scripts/episode/takes_r2v.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_a_cached_wav_of_the_right_length_is_reused(tk, tmp_path, monkeypatch):
    out = tmp_path / "silence_02.wav"
    out.write_bytes(b"RIFF")
    monkeypatch.setattr(tk, "clip_seconds", lambda p: 6.583)
    ran = []
    monkeypatch.setattr(tk.subprocess, "run", lambda *a, **k: ran.append(a))
    assert tk.composite([], 6.583, out) == out
    assert ran == []


def test_a_cached_wav_of_the_WRONG_length_is_rebuilt(tk, tmp_path, monkeypatch):
    """The ep03 case exactly: a 12.25 s guide left over a 6.583 s take."""
    out = tmp_path / "silence_02.wav"
    out.write_bytes(b"RIFF")
    monkeypatch.setattr(tk, "clip_seconds", lambda p: 12.25)
    ran = []
    monkeypatch.setattr(tk.subprocess, "run", lambda *a, **k: ran.append(a))
    tk.composite([], 6.583, out)
    assert ran, "a guide of the wrong length must be rebuilt, not reused"


def test_a_wav_that_is_too_SHORT_is_rebuilt(tk, tmp_path, monkeypatch):
    """The dangerous direction: the model's clock would stop before the picture."""
    out = tmp_path / "silence_02.wav"
    out.write_bytes(b"RIFF")
    monkeypatch.setattr(tk, "clip_seconds", lambda p: 4.0)
    ran = []
    monkeypatch.setattr(tk.subprocess, "run", lambda *a, **k: ran.append(a))
    tk.composite([], 6.583, out)
    assert ran


def test_a_frame_of_slack_is_tolerated(tk, tmp_path, monkeypatch):
    """`clip_seconds` reads ffmpeg's two-decimal clock, so an exact compare would
    rebuild every take on every run."""
    out = tmp_path / "silence_02.wav"
    out.write_bytes(b"RIFF")
    monkeypatch.setattr(tk, "clip_seconds", lambda p: 6.58)
    ran = []
    monkeypatch.setattr(tk.subprocess, "run", lambda *a, **k: ran.append(a))
    assert tk.composite([], 6.583, out) == out
    assert ran == []


def test_an_unreadable_cached_wav_is_rebuilt_rather_than_trusted(tk, tmp_path, monkeypatch):
    """Being unable to measure is not a pass -- `bed_gate`'s rule, applied here."""
    out = tmp_path / "silence_02.wav"
    out.write_bytes(b"not a wav")

    def boom(_):
        raise ValueError("no duration")

    monkeypatch.setattr(tk, "clip_seconds", boom)
    ran = []
    monkeypatch.setattr(tk.subprocess, "run", lambda *a, **k: ran.append(a))
    tk.composite([], 6.583, out)
    assert ran
