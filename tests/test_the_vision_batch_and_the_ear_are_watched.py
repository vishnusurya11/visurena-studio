"""Watchdogs on the take content VL batch and on the QC ear (package H, retro 2026-10-20).

A VL frame read waited up to 600 s (comfy.run_text) and the GPU whisper worker's readline() had
no deadline at all.  A stalled frame read now frees the engine and asks once more (a second
stall raises, as a 600 s timeout did); a clip the worker does not answer drops the worker, so the
routed ear's CPU fallback hears it.  No engine, no GPU: every call is faked.
"""
from __future__ import annotations

import inspect
import sys
import threading
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "episode"))
import qc  # noqa: E402
import take_content_check as tcc  # noqa: E402
from studio import comfy  # noqa: E402


def engine(monkeypatch, answers: list, frees: list, asked: list) -> None:
    def cached_text(name, values, readable, timeout=600.0):
        asked.append(timeout)
        got = answers.pop(0)
        if isinstance(got, Exception):
            raise got
        return got
    monkeypatch.setattr(tcc.comfy, "cached_text", cached_text)
    monkeypatch.setattr(tcc.comfy, "stage_image", lambda path: Path(path).name)
    monkeypatch.setattr(tcc.comfy, "free_models", lambda: frees.append("free"))
    monkeypatch.setattr(tcc.pc, "parse", lambda said: said)


def test_a_frame_read_has_a_deadline_and_one_more_ask_after_a_free(monkeypatch):
    frees, asked = [], []
    engine(monkeypatch, [comfy.StillRunning("p", tcc.FRAME_READ_S), "a man at a door"], frees, asked)
    assert tcc.read_frame(Path("T00_0.png"), seed=11) == "a man at a door"
    assert frees == ["free"] and asked == [tcc.FRAME_READ_S, tcc.FRAME_READ_S]


def test_a_second_stall_raises_as_the_old_timeout_did(monkeypatch):
    frees, asked = [], []
    engine(monkeypatch, [comfy.StillRunning("p", 1.0), comfy.StillRunning("p", 1.0)], frees, asked)
    with pytest.raises(comfy.StillRunning):
        tcc.read_frame(Path("T00_0.png"), seed=11)


def test_the_twin_ask_is_watched_too(monkeypatch):
    frees, asked = [], []
    engine(monkeypatch, [comfy.StillRunning("p", 1.0), "two"], frees, asked)
    monkeypatch.setattr(tcc.pc, "parse_twins", lambda said: said)
    assert tcc.read_twin_frame(Path("T00_0.png"), seed=23) == "two" and frees == ["free"]


class StuckEar:
    """A routed ear whose GPU worker never answers until it is dropped; then the CPU hears."""

    def __init__(self):
        self.worker, self.gone, self.dropped = object(), threading.Event(), 0

    def __call__(self, clip):
        if not self.gone.wait(timeout=5):
            return "the watchdog never fired"
        return "heard on the cpu"

    def drop(self):
        self.dropped += 1
        self.worker = None
        self.gone.set()


def test_a_silent_worker_is_dropped_and_the_cpu_hears_the_clip(capsys):
    ear = StuckEar()
    assert qc.watched(ear, seconds=0.05)(Path("qc_l03.wav")) == "heard on the cpu"
    assert ear.dropped == 1 and "WATCHDOG whisper: qc_l03.wav" in capsys.readouterr().out


def test_a_prompt_answer_drops_nothing():
    ear = StuckEar()
    ear.gone.set()
    assert qc.watched(ear, seconds=0.05)(Path("a.wav")) == "heard on the cpu"
    threading.Event().wait(0.1)
    assert ear.dropped == 0


def test_a_cpu_ear_has_nothing_to_drop(capsys):
    def slow(clip):
        return threading.Event().wait(0.2) or "cpu"
    assert qc.watched(slow, seconds=0.05)(Path("b.wav")) == "cpu"
    assert "no GPU worker to drop" in capsys.readouterr().out


def test_qc_hears_through_the_watchdog():
    assert "watched(voice_qc.any_transcriber())" in inspect.getsource(qc.main)
