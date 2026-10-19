"""The ear, routed (owner 2026-10-18: GPU when idle, CPU when rendering).

`routed(cpu_factory)` asks the device router once for the batch.  On "cpu" it hands
back `cpu_factory()` itself -- today's ear, byte for byte.  On "cuda" it starts the
whisper worker under ComfyUI's embedded python (studio/whisper_worker: the same
large-v3-turbo weights, fp16 on the card) holding a GPU claim, and before every clip
looks at the ComfyUI queue: a render that arrived closes the worker and the rest of
the batch goes to the CPU ear.  A worker that cannot start, never says ready, dies or
answers an error is the CPU's too -- the gate is never left without an ear.
"""
from __future__ import annotations

import atexit
import json
import subprocess
from contextlib import ExitStack
from pathlib import Path
from typing import Callable

WHISPER_GB = 4.0
"""large-v3-turbo fp16 on the card with its decoder buffers, and room."""
AGREE = 0.10
"""How far apart (word error rate) the GPU's fp16 and the CPU's fp32 transcript of
one clip may read; measured on Jekyll ep01's lines 2026-10-18 (fixture)."""
Ear = Callable[[Path], str]


def worker_argv(python: Path, model: str, root: str) -> list[str]:
    return [str(python), "-I", str(Path(__file__).with_name("whisper_worker.py")), model, root]


def spawn_worker() -> subprocess.Popen:
    """The worker under the portable python, with the voice gate's model and weights."""
    from studio import master_upscale, voice_qc
    python = master_upscale.av3_paths()[0]
    return subprocess.Popen(worker_argv(python, voice_qc.MODEL, voice_qc.WHISPER_ROOT), stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, text=True, encoding="utf-8")


class Worker:
    """One started worker process, asked one clip at a time."""

    def __init__(self, proc):
        self.proc = proc
        if json.loads(proc.stdout.readline() or "{}").get("ready") is not True:
            self.close()
            raise RuntimeError("the whisper worker never said ready")

    def __call__(self, clip: Path) -> str:
        self.proc.stdin.write(json.dumps({"clip": str(clip)}) + "\n")
        self.proc.stdin.flush()
        said = json.loads(self.proc.stdout.readline() or '{"error": "the worker died"}')
        if "text" not in said:
            raise RuntimeError(said.get("error", "no text"))
        return said["text"].strip()

    def close(self) -> None:
        try:
            self.proc.stdin.close()
            self.proc.wait(timeout=10)
        except Exception:
            self.proc.kill()


class Routed:
    """The batch's ear: the worker while the GPU stays free, the CPU ear after."""

    def __init__(self, cpu_factory: Callable[[], Ear], worker: Worker, held: ExitStack, busy: Callable[[], bool]):
        self.cpu_factory, self.worker, self.held, self.busy, self.cpu = cpu_factory, worker, held, busy, None
        atexit.register(self.drop)

    def __call__(self, clip: Path) -> str:
        if self.worker is not None and self.busy():
            print("DEVICE whisper -> cpu: render arrived mid-batch", flush=True)
            self.drop()
        if self.worker is not None:
            try:
                return self.worker(clip)
            except Exception as failed:
                print(f"DEVICE whisper -> cpu: worker failed ({failed})", flush=True)
                self.drop()
        self.cpu = self.cpu or self.cpu_factory()
        return self.cpu(clip)

    def drop(self) -> None:
        if self.worker is not None:
            self.worker.close()
            self.worker = None
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
           busy: Callable[[], bool] | None = None) -> Ear:
    """Today's ear on "cpu"; the GPU worker (with the CPU ear behind it) on "cuda"."""
    if route is None:
        from studio.compute_device import device_for as route
    if route("whisper", WHISPER_GB) != "cuda":
        return cpu_factory()
    held = ExitStack()
    worker = started(spawn or spawn_worker, held)
    return Routed(cpu_factory, worker, held, busy or queue_busy)
