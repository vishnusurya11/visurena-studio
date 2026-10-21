"""The fake workers' memos are filled by the REAL workers on the CPU (DESIGN 2.3, R11;
2026-10-21_ep02_proof P4): scripts/proof/fill_memos.py runs face_detect's YOLO worker and the
CPU whisper ear over recorded/served takes and wavs, keyed exactly as the fake workers look
them up, and only while ComfyUI is idle.

The default run tests the filler's logic with fake readers ($0, no model).  The one test that
runs the real CPU models is `@pytest.mark.local`: free, slow, never in the default run."""
from __future__ import annotations

import json
import shutil
import subprocess
import wave
from pathlib import Path

import pytest

from scripts.proof import fill_memos
from studio.rehearsal import fake_workers


def put(path: Path, data: bytes) -> Path:
    path.write_bytes(data)
    return path


def test_the_filler_keys_exactly_as_the_fake_workers_look_up(tmp_path):
    wav, take = put(tmp_path / "a.wav", b"w"), put(tmp_path / "T01.mp4", b"t")
    got = fill_memos.fill(tmp_path / "memos", whisper=[wav], detect=[take],
                          hear=lambda p: "heard", see=lambda p: {"0": []}, idle=lambda: True)
    assert json.loads((tmp_path / "memos" / "whisper.json").read_text(encoding="utf-8")) == {fake_workers.file_key(wav): "heard"}
    detect = json.loads((tmp_path / "memos" / "detect.json").read_text(encoding="utf-8"))
    assert list(detect) == [fake_workers.detect_key(take, fake_workers.detect_every())]
    assert got["whisper"]["filled"] == 1 and got["detect"]["seconds"] >= 0


def test_a_filled_memo_is_merged_never_rewritten(tmp_path):
    a, b = put(tmp_path / "a.wav", b"a"), put(tmp_path / "b.wav", b"b")
    fill_memos.fill(tmp_path / "memos", whisper=[a], hear=lambda p: "first", idle=lambda: True)
    asked = []
    fill_memos.fill(tmp_path / "memos", whisper=[a, b], hear=lambda p: asked.append(p) or "second", idle=lambda: True)
    memo = json.loads((tmp_path / "memos" / "whisper.json").read_text(encoding="utf-8"))
    assert memo == {fake_workers.file_key(a): "first", fake_workers.file_key(b): "second"} and asked == [b]


def test_a_busy_engine_refuses_the_fill(tmp_path):
    with pytest.raises(fill_memos.EngineBusy):
        fill_memos.fill(tmp_path / "memos", whisper=[put(tmp_path / "a.wav", b"a")], hear=str, idle=lambda: False)
    assert not (tmp_path / "memos" / "whisper.json").exists()


def test_the_engine_is_idle_only_when_its_queue_is_empty_or_it_is_not_running():
    assert fill_memos.engine_idle(lambda: (0, 0)) is True
    assert fill_memos.engine_idle(lambda: (1, 0)) is False
    assert fill_memos.engine_idle(_refused) is True
    assert fill_memos.engine_idle(lambda: (_ for _ in ()).throw(ValueError("garbled"))) is False


def _refused():
    raise ConnectionRefusedError("no engine on :8188")


def test_the_real_workers_run_on_the_cpu_and_never_phone_home():
    env = fill_memos.cpu_env({"CUDA_VISIBLE_DEVICES": "0"})
    assert env["CUDA_VISIBLE_DEVICES"] == "" and env["YOLO_OFFLINE"] == "1"


def test_the_cli_names_what_it_fills(tmp_path, monkeypatch, capsys):
    wav = put(tmp_path / "a.wav", b"a")
    monkeypatch.setattr(fill_memos, "real_ear", lambda: (lambda p: "x"))
    monkeypatch.setattr(fill_memos, "engine_idle", lambda fetch=None: True)
    assert fill_memos.main([str(tmp_path / "memos"), "--whisper", str(wav)]) == 0
    assert "whisper: 1 filled" in capsys.readouterr().out


@pytest.mark.local
def test_the_real_cpu_workers_fill_one_wav_and_one_take(tmp_path):
    wav = tmp_path / "silence.wav"
    with wave.open(str(wav), "wb") as out:
        out.setnchannels(1), out.setsampwidth(2), out.setframerate(16000)
        out.writeframes(b"\0\0" * 16000)
    take = tmp_path / "T01.mp4"
    subprocess.run([shutil.which("ffmpeg") or "ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
                    "color=c=gray:s=128x128:d=0.5", str(take)], check=True)
    got = fill_memos.fill(tmp_path / "memos", whisper=[wav], detect=[take])
    assert got["whisper"]["filled"] == 1 and got["detect"]["filled"] == 1
    print(json.dumps(got))
