"""The ear, routed (owner 2026-10-18: GPU when idle, CPU when rendering).

`routed(cpu_factory)` asks the device router once for the batch.  On "cpu" it hands
back `cpu_factory()` itself -- today's ear, byte for byte.  On "cuda" it returns a
`Routed` ear that starts the whisper worker under ComfyUI's embedded python
(studio/whisper_worker: the same large-v3-turbo weights, fp16 on the card) AT THE
FIRST CLIP, holding a GPU claim, and before every clip looks at the ComfyUI queue: a
render that arrived closes the worker and the rest of the batch goes to the CPU ear.

A32 (face debate 2026-10-21, LEDGER_round4 check 3): ep01 run01 spawned the worker before any
clip was cut; it idled past IDLE_S = 30 s, the first write read `[Errno 22]`, and one line took
527 s on the CPU ear.  So the worker is spawned lazily, a worker that dies is spawned ONCE more
(its `poll()` printed) before the CPU ear, and its stderr goes to `review/work/qc_whisper.err`.
A worker that cannot start, never says ready, dies twice or answers an error is the CPU's -- the
gate is never left without an ear.
"""
from __future__ import annotations

import atexit
import json
import subprocess
from contextlib import ExitStack
from pathlib import Path
from typing import Callable

IDLE_S = 30.0
"""Mirror of studio/whisper_worker.IDLE_S (that file runs under another python, so it is not imported)."""
WHISPER_GB = 4.0
"""large-v3-turbo fp16 on the card with its decoder buffers, and room."""
AGREE = 0.10
"""How far apart (word error rate) the GPU's fp16 and the CPU's fp32 transcript of
one clip may read; measured on Jekyll ep01's lines 2026-10-18 (fixture)."""
SPAWNS = 2
"""The worker is started at most twice a batch: once, and once more after a death (A32)."""
ERR_LOG = Path("review") / "work" / "qc_whisper.err"
Ear = Callable[[Path], str]


def worker_argv(python: Path, model: str, root: str) -> list[str]:
    return [str(python), "-I", str(Path(__file__).with_name("whisper_worker.py")), model, root]


def err_log(home: Path) -> Path:
    """Where the worker's stderr goes for an episode (its CUDA and whisper complaints)."""
    return Path(home) / ERR_LOG


def popen_kwargs(err_path: Path | None = None) -> dict:
    """The pipes a worker is started with; stderr appended to `err_path` when one is named."""
    out = {"stdin": subprocess.PIPE, "stdout": subprocess.PIPE, "text": True, "encoding": "utf-8"}
    if err_path is not None:
        Path(err_path).parent.mkdir(parents=True, exist_ok=True)
        out["stderr"] = open(err_path, "a", encoding="utf-8")
    return out


def spawn_worker(err_path: Path | None = None) -> subprocess.Popen:
    """The worker under the portable python, with the voice gate's model and weights."""
    from studio import master_upscale, voice_qc
    python = master_upscale.av3_paths()[0]
    return subprocess.Popen(worker_argv(python, voice_qc.MODEL, voice_qc.WHISPER_ROOT), **popen_kwargs(err_path))


class Worker:
    """One started worker process, asked one clip at a time."""

    def __init__(self, proc):
        self.proc = proc
        if json.loads(proc.stdout.readline() or "{}").get("ready") is not True:
            self.close()
            raise RuntimeError("the whisper worker never said ready")

    def ask(self, clip: Path) -> None:
        """Send one clip; a worker already gone is named, not left to a write error."""
        gone = self.proc.poll()
        if gone is not None:
            raise RuntimeError(f"the whisper worker had exited (code {gone}) before this clip; it leaves "
                               f"after {IDLE_S:.0f} s idle, so a gap between clips longer than that ends it")
        try:
            self.proc.stdin.write(json.dumps({"clip": str(clip)}) + "\n")
            self.proc.stdin.flush()
        except OSError as failed:                  # Windows says [Errno 22] for a pipe nobody reads
            raise RuntimeError(f"the whisper worker closed its input pipe ({failed}); "
                               "it had exited or was exiting") from failed

    def __call__(self, clip: Path) -> str:
        self.ask(clip)
        said = json.loads(self.proc.stdout.readline() or '{"error": "the worker died"}')
        if "text" not in said:
            raise RuntimeError(said.get("error", "no text"))
        return said["text"].strip()

    def poll(self):
        return self.proc.poll()

    def close(self) -> None:
        try:
            self.proc.stdin.close()
            self.proc.wait(timeout=10)
        except Exception:
            self.proc.kill()


class Routed:
    """The batch's ear: the worker while the GPU stays free (started at the first clip, started once
    more after a death), the CPU ear after."""

    def __init__(self, cpu_factory: Callable[[], Ear], spawn: Callable, held: ExitStack, busy: Callable[[], bool]):
        self.cpu_factory, self.spawn, self.held, self.busy = cpu_factory, spawn, held, busy
        self.worker, self.cpu, self.spawns, self.gpu_done = None, None, 0, False
        atexit.register(self.drop)

    def __call__(self, clip: Path) -> str:
        if not self.gpu_done and self.busy():
            print("DEVICE whisper -> cpu: render arrived mid-batch", flush=True)
            self.drop()
        while not self.gpu_done:
            try:
                return self.ready()(clip)
            except Exception as failed:
                self.failed(failed)
        self.cpu = self.cpu or self.cpu_factory()
        return self.cpu(clip)

    def ready(self) -> Worker:
        """The live worker, started on demand; past SPAWNS starts the GPU is done for the batch."""
        if self.worker is None:
            if self.spawns >= SPAWNS:
                raise RuntimeError(f"the worker was started {SPAWNS} times this batch")
            self.spawns += 1
            self.worker = started(self.spawn, self.held)
            if self.worker is None:
                raise RuntimeError("the worker would not start")
        return self.worker

    def failed(self, failed: Exception) -> None:
        """A dead or failing worker: its exit code printed; one respawn, then the CPU ear."""
        code = self.worker.poll() if self.worker is not None else None
        again = self.spawns < SPAWNS
        print(f"DEVICE whisper worker failed ({failed}); poll() = {code}; "
              f"{'one respawn' if again else 'no respawn left -> cpu'}", flush=True)
        self.close_worker()
        if not again:
            self.drop()

    def close_worker(self) -> None:
        if self.worker is not None:
            self.worker.close()
            self.worker = None

    def drop(self) -> None:
        """The GPU is done for this batch: the worker closed, the claim released."""
        self.close_worker()
        self.gpu_done = True
        self.held.close()


def queue_busy() -> bool:
    from studio import comfy
    try:
        return comfy.busy()
    except Exception:                       # an engine that answers wrong is not idle
        return True


def started(spawn: Callable, held: ExitStack) -> Worker | None:
    """The worker, holding the GPU claim; None (claim released) when it will not start."""
    from studio import compute_device
    held.enter_context(compute_device.claim("whisper worker"))
    try:
        return Worker(spawn())
    except Exception as failed:
        print(f"DEVICE whisper -> cpu: worker would not start ({failed})", flush=True)
        held.close()
        return None


def routed(cpu_factory: Callable[[], Ear], route: Callable | None = None, spawn: Callable | None = None,
           busy: Callable[[], bool] | None = None, err_path: Path | None = None) -> Ear:
    """Today's ear on "cpu"; the GPU worker (with the CPU ear behind it) on "cuda"."""
    if route is None:
        from studio.compute_device import device_for as route
    if route("whisper", WHISPER_GB) != "cuda":
        return cpu_factory()
    return Routed(cpu_factory, spawn or (lambda: spawn_worker(err_path)), ExitStack(), busy or queue_busy)
