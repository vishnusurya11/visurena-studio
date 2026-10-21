"""Whisper follows the device router (owner 2026-10-18): on an idle GPU the ear is a
worker under ComfyUI's embedded python (CUDA torch + openai-whisper, the same
large-v3-turbo weights); while a render runs it is today's CPU ear, unchanged.

A render that arrives mid-batch sends the rest of the batch to the CPU and the
worker is closed (its VRAM back to the render).  A worker that dies is the CPU's
too.  No test spawns a worker or loads weights: the worker is a fake process."""
from __future__ import annotations

import io
import json
from pathlib import Path

import pytest

from studio import routed_whisper as rw
from studio import voice_qc

PAIR = Path(__file__).parent / "fixtures" / "compute_device" / "whisper_cpu_vs_gpu.json"


@pytest.fixture(autouse=True)
def claims_in_tmp(tmp_path, monkeypatch):
    """The worker's GPU claim lands in the test's folder, never the studio's."""
    from studio import compute_device
    monkeypatch.setattr(compute_device, "CLAIMS", tmp_path / "claims")


class FakeProc:
    """A worker process speaking the line protocol: ready, then one answer per ask."""

    def __init__(self, answers: list[dict], ready: bool = True):
        out = ([json.dumps({"ready": True})] if ready else []) + [json.dumps(a) for a in answers]
        self.stdout = io.StringIO("".join(line + "\n" for line in out))
        self.stdin = io.StringIO()
        self.closed = False

    def poll(self):
        return 0 if self.closed else None

    def kill(self):
        self.closed = True

    def wait(self, timeout=None):
        self.closed = self.stdin.closed     # the worker exits on EOF
        return 0


def cpu_ear(heard: list):
    def factory():
        def listen(clip):
            heard.append(Path(clip).name)
            return "cpu words"
        return listen
    return factory


def test_the_cpu_route_hands_back_todays_ear_itself():
    def todays(clip):
        return "today"
    got = rw.routed(lambda: todays, route=lambda job, gb: "cpu")
    assert got is todays


def test_the_cuda_route_listens_through_the_worker():
    proc = FakeProc([{"text": "  gpu words "}])
    listen = rw.routed(cpu_ear([]), route=lambda job, gb: "cuda", spawn=lambda: proc, busy=lambda: False)
    assert listen(Path("a.wav")) == "gpu words"
    assert json.loads(proc.stdin.getvalue().splitlines()[0]) == {"clip": str(Path("a.wav"))}


def test_a_render_arriving_mid_batch_sends_the_rest_to_the_cpu_and_closes_the_worker():
    proc, heard, queue = FakeProc([{"text": "one"}, {"text": "two"}]), [], iter([False, True])
    listen = rw.routed(cpu_ear(heard), route=lambda job, gb: "cuda", spawn=lambda: proc,
                       busy=lambda: next(queue))
    assert listen(Path("a.wav")) == "one"
    assert listen(Path("b.wav")) == "cpu words"
    assert heard == ["b.wav"] and proc.closed


def test_a_worker_error_falls_back_to_the_cpu_for_that_clip():
    proc, heard = FakeProc([{"error": "CUDA out of memory"}]), []
    listen = rw.routed(cpu_ear(heard), route=lambda job, gb: "cuda", spawn=lambda: proc, busy=lambda: False)
    assert listen(Path("a.wav")) == "cpu words" and heard == ["a.wav"] and proc.closed


def test_a_worker_that_never_says_ready_is_the_cpus():
    heard = []
    listen = rw.routed(cpu_ear(heard), route=lambda job, gb: "cuda", spawn=lambda: FakeProc([], ready=False),
                       busy=lambda: False)
    assert listen(Path("a.wav")) == "cpu words"


def test_a_worker_that_cannot_start_is_the_cpus():
    def broken():
        raise OSError("no portable python")
    heard = []
    listen = rw.routed(cpu_ear(heard), route=lambda job, gb: "cuda", spawn=broken, busy=lambda: False)
    assert listen(Path("a.wav")) == "cpu words"


def test_the_worker_is_launched_isolated_under_the_portable_python():
    argv = rw.worker_argv(Path("P/python.exe"), "large-v3-turbo", "W")
    assert argv[:2] == [str(Path("P/python.exe")), "-I"]
    assert argv[2].endswith("whisper_worker.py") and argv[3:] == ["large-v3-turbo", "W"]


def test_the_worker_answers_one_line_per_clip_and_reports_errors():
    from studio import whisper_worker as ww

    def engine(path):
        if path == "bad.wav":
            raise RuntimeError("boom")
        return {"text": f" heard {path} "}
    out = io.StringIO()
    ww.serve(io.StringIO('{"clip": "a.wav"}\n{"clip": "bad.wav"}\n'), out, engine)
    rows = [json.loads(l) for l in out.getvalue().splitlines()]
    assert rows == [{"text": "heard a.wav"}, {"error": "RuntimeError: boom"}]


def test_any_transcriber_asks_the_router():
    asked = []
    voice_qc_route = rw.routed

    def fake_routed(cpu_factory, **kw):
        asked.append(cpu_factory)
        return "ear"
    rw.routed = fake_routed
    try:
        assert voice_qc.any_transcriber() == "ear"
    finally:
        rw.routed = voice_qc_route
    assert asked and asked[0] is voice_qc.cpu_transcriber


# -- the recorded pair: CPU fp32 and GPU fp16 heard the same ep01 lines --------------

@pytest.mark.skipif(not PAIR.exists(), reason="the recorded pair is written by the 2026-10-18 measure")
def test_gpu_and_cpu_transcripts_agree_within_tolerance():
    rows = json.loads(PAIR.read_text(encoding="utf-8"))["clips"]
    assert rows
    for row in rows:
        apart = voice_qc.error_rate(row["gpu"], row["cpu"])
        assert apart <= rw.AGREE, f"{row['clip']}: {apart:.2f} apart: {row['gpu']!r} vs {row['cpu']!r}"
        assert (voice_qc.error_rate(row["gpu"], row["intended"]) <= voice_qc.MAX_ERROR_RATE) == \
               (voice_qc.error_rate(row["cpu"], row["intended"]) <= voice_qc.MAX_ERROR_RATE)


class DeadPipe(io.StringIO):
    """A stdin whose reader is gone: Windows answers a write to it [Errno 22], not BrokenPipe."""

    def write(self, text):
        raise OSError(22, "Invalid argument")


def test_a_worker_that_idled_out_is_named_not_errno_22():
    """ep01 step 11: the worker left after IDLE_S, the next write read '[Errno 22] Invalid argument'."""
    proc, heard = FakeProc([{"text": "x"}]), []
    listen = rw.routed(cpu_ear(heard), route=lambda job, gb: "cuda", spawn=lambda: proc, busy=lambda: False)
    proc.closed = True                                      # exited between clips; poll() -> 0
    assert listen(Path("a.wav")) == "cpu words" and heard == ["a.wav"]


def test_the_failure_message_names_the_exit_and_the_idle_limit(capsys):
    proc = FakeProc([{"text": "x"}])
    listen = rw.routed(cpu_ear([]), route=lambda job, gb: "cuda", spawn=lambda: proc, busy=lambda: False)
    proc.closed = True
    listen(Path("a.wav"))
    said = capsys.readouterr().out
    assert "exited" in said and "idle" in said and "Errno 22" not in said


def test_a_dead_pipe_write_is_named_even_when_the_exit_is_not_yet_seen(capsys):
    proc = FakeProc([{"text": "x"}])
    listen = rw.routed(cpu_ear([]), route=lambda job, gb: "cuda", spawn=lambda: proc, busy=lambda: False)
    proc.stdin = DeadPipe()
    assert listen(Path("a.wav")) == "cpu words"
    said = capsys.readouterr().out
    assert "closed its input" in said and "Errno 22" in said


def test_the_message_quotes_the_workers_real_idle_limit():
    from studio import whisper_worker
    assert rw.IDLE_S == whisper_worker.IDLE_S


# ---- A32 (face debate 2026-10-21, LEDGER_round4 check 3 + A32) --------------------------------------

def spawner(procs: list):
    made = []

    def spawn():
        made.append(len(made))
        return procs[min(len(made) - 1, len(procs) - 1)]
    spawn.made = made
    return spawn


def test_the_worker_is_spawned_at_the_first_clip_not_at_the_router():
    """ep01 run01: the worker started before any clip was cut, idled past IDLE_S = 30 s and the first
    write read [Errno 22]; 527 s on the CPU ear followed."""
    spawn = spawner([FakeProc([{"text": "one"}])])
    listen = rw.routed(cpu_ear([]), route=lambda job, gb: "cuda", spawn=spawn, busy=lambda: False)
    assert spawn.made == []
    assert listen(Path("a.wav")) == "one" and spawn.made == [0]


def test_a_worker_that_died_is_spawned_once_more_before_the_cpu_ear():
    dead, live, heard = FakeProc([{"text": "x"}]), FakeProc([{"text": "gpu words"}]), []
    dead.closed = True                                         # exited between its ready line and the clip
    spawn = spawner([dead, live])
    listen = rw.routed(cpu_ear(heard), route=lambda job, gb: "cuda", spawn=spawn, busy=lambda: False)
    assert listen(Path("a.wav")) == "gpu words" and heard == [] and spawn.made == [0, 1]


def test_a_second_death_is_the_cpus_and_no_third_worker_is_started():
    dead1, dead2, heard = FakeProc([{"text": "x"}]), FakeProc([{"text": "y"}]), []
    dead1.closed = dead2.closed = True
    spawn = spawner([dead1, dead2])
    listen = rw.routed(cpu_ear(heard), route=lambda job, gb: "cuda", spawn=spawn, busy=lambda: False)
    assert listen(Path("a.wav")) == "cpu words" and heard == ["a.wav"] and spawn.made == [0, 1]
    assert listen(Path("b.wav")) == "cpu words" and spawn.made == [0, 1]


def test_the_failure_line_names_the_workers_exit_code(capsys):
    dead = FakeProc([{"text": "x"}])
    dead.closed = True
    listen = rw.routed(cpu_ear([]), route=lambda job, gb: "cuda", spawn=spawner([dead, dead]), busy=lambda: False)
    listen(Path("a.wav"))
    said = capsys.readouterr().out
    assert "poll() = 0" in said and "respawn" in said.lower()


def test_the_workers_stderr_goes_to_the_episodes_qc_log(tmp_path):
    home = tmp_path / "ep01"
    assert rw.err_log(home) == home / "review" / "work" / "qc_whisper.err"
    kw = rw.popen_kwargs(rw.err_log(home))
    assert kw["stderr"].name == str(home / "review" / "work" / "qc_whisper.err") and kw["text"] is True
    kw["stderr"].close()
