"""A2 (fleet E, 2026-10-22): every clip the ear hears writes one row.

VL reads have vlm_calls.jsonl (comfy.log_call); whisper had nothing, so the split between TTS
and listening in step 04 was never measured (the gate on a pipelined listen, fleet E ruling).
`library/whisper_calls.jsonl` gets one row per heard clip: the device, the clip's name, the
seconds and the words.  A log that cannot be written never fails the ear."""
from __future__ import annotations

import io
import json
from pathlib import Path

from studio import routed_whisper as rw
from studio import voice_qc


class Proc:
    def __init__(self, answers):
        lines = [json.dumps({"ready": True})] + [json.dumps(a) for a in answers]
        self.stdout = io.StringIO("".join(line + "\n" for line in lines))
        self.stdin = io.StringIO()

    def poll(self):
        return None


class Engine:
    def transcribe(self, clip, **options):
        return {"text": " cpu words here "}


def rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_the_gpu_worker_writes_a_row_per_clip(tmp_path, monkeypatch):
    monkeypatch.setattr(rw, "WHISPER_CALLS", tmp_path / "whisper_calls.jsonl")
    ear = rw.Worker(Proc([{"text": " two words "}]))
    assert ear(tmp_path / "l03.wav") == "two words"
    got, = rows(tmp_path / "whisper_calls.jsonl")
    assert (got["device"], got["clip"], got["words"]) == ("cuda", "l03.wav", 2) and got["seconds"] >= 0


def test_the_cpu_ear_writes_a_row_per_clip(tmp_path, monkeypatch):
    monkeypatch.setattr(rw, "WHISPER_CALLS", tmp_path / "whisper_calls.jsonl")
    monkeypatch.setitem(voice_qc._HEARD, (voice_qc.MODEL, "cpu"), Engine())
    assert voice_qc.transcriber(device="cpu")(tmp_path / "l04.wav") == "cpu words here"
    got, = rows(tmp_path / "whisper_calls.jsonl")
    assert (got["device"], got["clip"], got["words"]) == ("cpu", "l04.wav", 3)


def test_a_log_that_cannot_be_written_never_fails_the_ear(tmp_path, monkeypatch):
    monkeypatch.setattr(rw, "WHISPER_CALLS", tmp_path)               # a folder: open() raises
    assert rw.Worker(Proc([{"text": "fine"}]))(tmp_path / "a.wav") == "fine"
