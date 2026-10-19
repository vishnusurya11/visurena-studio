"""The av3 master pass never hangs (Jekyll ep01 2026-10-18 21:45: 3,259 of 3,348 frames
encoded, then the worker sat in `dec.wait()` for good).  Root cause: anything raised
inside the pump closed the encoder cleanly but left the decoder and the per-shot
denoise blocked on full pipes nobody read, and `streamed` waited on the decoder
forever -- hiding the very error that stopped it.  Now a failure kills the pipeline
and surfaces; a pump that moves no frame for STALL_S is killed by a watchdog, and the
repo falls back to rtx4x (lanczos without RTX), saying so.

The owner's order of the same evening: the face paste happens at CUT resolution,
before the one upscale, and nothing edits picture after it.

ffmpeg on tiny synthetic clips, CPU only: free, no GPU, no weights."""
from __future__ import annotations

import functools
import subprocess
import sys
import threading
import time
from contextlib import nullcontext
from pathlib import Path

import numpy as np
import pytest

from studio import face_paste as fp
from studio import master_av3 as av
from studio import master_upscale as mu

SIDE = 32


def parts(tmp_path, seconds=(40, 40, 30)):
    """A multi-shot cut: thousands of small frames across three parts, with sound."""
    out = []
    for k, s in enumerate(seconds):
        path = tmp_path / f"p{k}.mp4"
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"testsrc=s={SIDE}x{SIDE}:r=24:d={s}",
                        "-f", "lavfi", "-t", str(s), "-i", "sine=f=440:r=48000", "-c:v", "libx264",
                        "-preset", "ultrafast", "-pix_fmt", "yuv420p", "-c:a", "aac", "-ar", "48000", str(path)],
                       check=True)
        out.append(path)
    listing = tmp_path / "l.txt"
    listing.write_text("".join(f"file '{p.as_posix()}'\n" for p in out), encoding="utf-8")
    return listing


def within(seconds, fn):
    """fn() on a daemon thread; ('hung', None) when it has not returned in time."""
    box = {}

    def go():
        try:
            box["value"] = fn()
        except BaseException as failed:   # the test reads what was raised
            box["error"] = failed
    t = threading.Thread(target=go, daemon=True)
    t.start()
    t.join(seconds)
    return ("hung", None) if t.is_alive() else ("error", box["error"]) if "error" in box else ("ok", box["value"])


def failing_at(n):
    seen = {"k": 0}

    def up(frame):
        seen["k"] += 1
        if seen["k"] == n:
            raise RuntimeError("CUDA error: the card went away")
        return frame
    return up


def test_a_failure_mid_stream_kills_the_pipeline_and_surfaces(tmp_path):
    listing = parts(tmp_path)
    run = functools.partial(av.streamed, listing, tmp_path / "o.mp4", SIDE, SIDE, 1, 24, failing_at(1500),
                            [960, 1920])
    state, got = within(60, run)
    assert state == "error", f"the pass {state}: an error mid-stream must end it, not hang it"
    assert "card went away" in str(got)


def test_a_clean_multi_shot_pass_counts_every_frame(tmp_path):
    listing = parts(tmp_path, (10, 10, 5))
    state, got = within(60, lambda: av.streamed(listing, tmp_path / "o.mp4", SIDE, SIDE, 1, 24, lambda f: f,
                                                [240, 480]))
    assert (state, got) == ("ok", 600)


def stuck_decoder(frames: int) -> list[str]:
    """A decoder that hands out `frames` frames, then neither ends nor writes."""
    code = (f"import sys,time;sys.stdout.buffer.write(bytes({SIDE * SIDE * 3 * frames}));"
            "sys.stdout.buffer.flush();time.sleep(600)")
    return [sys.executable, "-c", code]


def test_a_pump_that_moves_nothing_is_killed_and_called_stalled(tmp_path, monkeypatch):
    listing = parts(tmp_path, (1,))
    monkeypatch.setattr(mu, "decode_argv", lambda *a: stuck_decoder(10))
    t0 = time.monotonic()
    state, got = within(45, lambda: av.streamed(listing, tmp_path / "o.mp4", SIDE, SIDE, 1, 24, lambda f: f,
                                                [], stall_s=1.5))
    assert state == "error" and isinstance(got, av.Stalled), (state, got)
    assert time.monotonic() - t0 < 30


def test_the_watchdog_fires_once_when_ticks_stop():
    fired = []
    dog = av.Watchdog(0.3, lambda: fired.append(1), poll=0.05)
    dog.start()
    for _ in range(6):
        dog.tick()
        time.sleep(0.1)
    assert not fired, "a pump that ticks is alive"
    time.sleep(0.8)
    dog.stop()
    assert fired == [1]


def test_a_stall_exits_the_worker_with_its_own_code(monkeypatch, capsys):
    def stalled(job, hard_exit=None):
        raise av.Stalled("no frame for 60 s")
    monkeypatch.setattr(av, "run", stalled)
    monkeypatch.setattr(av.Path, "read_text", lambda self, encoding=None: "{}")
    with pytest.raises(SystemExit) as out:
        av.main(["master_av3.py", "job.json"])
    assert out.value.code == av.STALLED
    assert "av3 stalled" in capsys.readouterr().err


# -- the repo side: a stalled worker falls back ---------------------------------------------

def a_worker(monkeypatch, tmp_path, code, rtx_reason=""):
    calls = []
    monkeypatch.setattr(mu, "av3_paths", lambda env=None: (tmp_path / "py.exe", tmp_path / "w.pth"))
    monkeypatch.setattr(mu, "run_worker", lambda python, job: code)
    monkeypatch.setattr(mu, "rtx_missing", lambda: rtx_reason)
    monkeypatch.setattr("studio.compute_device.claim", lambda job, root=None: nullcontext())
    monkeypatch.setattr(mu, "master", lambda *a, **k: calls.append((a, k)) or a[1])
    return calls


def fallback_of(tmp_path, monkeypatch, code, rtx_reason=""):
    calls = a_worker(monkeypatch, tmp_path, code, rtx_reason)
    mu.av3_master(tmp_path / "l.txt", tmp_path / "o.mp4", 768, 768, mu.CHOICES["av3"], 24, None, None, [5], "cuda")
    return calls


def test_a_stalled_worker_falls_back_to_rtx4x_and_says_so(tmp_path, monkeypatch, capsys):
    calls = fallback_of(tmp_path, monkeypatch, mu.AV3_STALLED)
    assert len(calls) == 1 and calls[0][0][4] == mu.CHOICES["rtx4x"]
    assert "CAP upscale: av3 stalled, fell back to rtx4x" in capsys.readouterr().err


def test_without_rtx_the_stall_falls_back_to_lanczos(tmp_path, monkeypatch, capsys):
    calls = fallback_of(tmp_path, monkeypatch, mu.AV3_STALLED, rtx_reason="no CUDA device")
    assert calls[0][0][4] == mu.LANCZOS
    assert "CAP upscale: av3 stalled, fell back to lanczos" in capsys.readouterr().err


def test_a_failed_worker_falls_back_too(tmp_path, monkeypatch, capsys):
    calls = fallback_of(tmp_path, monkeypatch, 1)
    assert calls[0][0][4] == mu.CHOICES["rtx4x"]
    assert "CAP upscale: av3 failed (exit 1), fell back to rtx4x" in capsys.readouterr().err


def test_a_finished_worker_falls_back_to_nothing(tmp_path, monkeypatch):
    assert fallback_of(tmp_path, monkeypatch, 0) == []


# -- the owner's order: paste at cut resolution, then the one upscale -----------------------

def test_the_upscaler_sees_the_pasted_cut_frame(tmp_path):
    listing = parts(tmp_path, (1,))
    seen = []

    def paste(frame):
        out = np.array(frame, copy=True)
        out[:] = 200
        return out

    def up(frame):
        seen.append((frame.shape, float(frame.mean())))
        return frame.repeat(2, axis=0).repeat(2, axis=1)
    av.streamed(listing, tmp_path / "o.mp4", SIDE, SIDE, 2, 24, up, [], paste=paste)
    assert len(seen) == 24 and {s for s, _ in seen} == {(SIDE, SIDE, 3)}
    assert all(abs(m - 200) < 2 for _, m in seen), "the paste reached the upscaler before the 2x"


def test_a_paster_wrap_becomes_a_cut_scale_paste():
    spans = [fp.Span(0, 0, 4, 0, 1.0, None, ())]
    wrap = functools.partial(fp.Paster, spans=spans, width=64, height=64, factor=4)
    paste = mu.at_cut(wrap)
    assert isinstance(paste, fp.Paster) and paste.factor == 1 and paste.spans == spans
    frame = np.zeros((64, 64, 3), np.uint8)
    assert paste(frame).shape == (64, 64, 3)


def test_no_wrap_is_no_paste():
    assert mu.at_cut(None) is None


def test_the_worker_pastes_at_cut_scale_before_the_model(tmp_path):
    crop = tmp_path / "crop.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "color=c=white:s=32x32:r=24:d=0.5",
                    "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", str(crop)], check=True)
    span = fp.Span(0, 0, 12, 0, 1.0, None, (fp.Track([(16, 8, 24)] * 12, (0, 11), 0, str(crop)),))
    job = {"spans": av.spans_json([span]), "width": 64, "height": 64, "factor": 4}
    paste = av.paste_of(job)
    assert isinstance(paste, fp.Paster) and paste.factor == 1
