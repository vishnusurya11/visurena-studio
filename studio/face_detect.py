"""The face refine's detector, routed (owner 2026-10-18: GPU when idle, CPU when rendering).

face_yolov8m.pt read Jekyll ep01's cel faces at 0.8+ confidence from 37 px up, where MTCNN
(a photo detector) dropped far figures and whole frames
(docs/audit/2026-10-19_face_blur/pipeline_audit.md sections 1-2).  It runs in a worker under
ComfyUI's embedded python (studio/face_detect_worker.py), one per refine run, asked one take
at a time.  The first start asks the device router; a GPU worker that sees a render arrive is
closed and the rest go to a CPU worker (the refine queues its own renders, so this is the
usual path after the first take).  A worker that will not start or answers an error hands
that take and every later one to MTCNN, said in the log -- the refine is never left blind.
"""
from __future__ import annotations

import atexit
import json
import os
import subprocess
from contextlib import ExitStack
from pathlib import Path
from typing import Callable

from studio.face_track import EVERY

CONF = 0.6
"""Mirror of studio/face_detect_worker.CONF (that file runs under another python)."""
THREADS = 4
"""Torch CPU threads: the take_dq lane runs beside it."""
YOLO_GB = 1.5
"""YOLOv8m at 768 with its CUDA context, and room."""
WEIGHTS = Path("ComfyUI") / "models" / "ultralytics" / "bbox" / "face_yolov8m.pt"
Dets = dict[int, list[dict]]


def weights_path(root: Path | None = None) -> Path:
    if root is None:
        from studio.engine_ops import portable_root
        root = portable_root(os.environ)
    return Path(root) / WEIGHTS


def worker_argv(python: Path, weights: Path, device: str) -> list[str]:
    return [str(python), "-I", str(Path(__file__).with_name("face_detect_worker.py")), str(weights), device,
            str(CONF), str(THREADS)]


def worker_env(device: str, env=None) -> dict:
    """The worker's environment: a CPU worker never opens the card, nothing phones home."""
    out = dict(os.environ if env is None else env) | {"YOLO_OFFLINE": "1"}
    return out | {"CUDA_VISIBLE_DEVICES": ""} if device == "cpu" else out


def spawn(device: str) -> subprocess.Popen:
    from studio import master_upscale
    python = master_upscale.av3_paths()[0]
    return subprocess.Popen(worker_argv(python, weights_path(), device), stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, text=True, encoding="utf-8", env=worker_env(device))


def parse(said: dict) -> Dets:
    """The worker's answer keyed by frame; an error answer raises."""
    if "dets" not in said:
        raise RuntimeError(said.get("error", "no answer"))
    return {int(t): list(found) for t, found in said["dets"].items()}


class Worker:
    """One started worker process, asked one take at a time."""

    def __init__(self, proc):
        self.proc = proc
        if json.loads(proc.stdout.readline() or "{}").get("ready") is not True:
            self.close()
            raise RuntimeError("the face detect worker never said ready")

    def exited(self) -> bool:
        """The worker left on its own (IDLE_S without a take, studio/face_detect_worker)."""
        return self.proc.poll() is not None

    def __call__(self, take: Path) -> Dets:
        if (gone := self.proc.poll()) is not None:
            raise RuntimeError(f"the face detect worker had exited (code {gone})")
        self.proc.stdin.write(json.dumps({"video": str(take), "every": EVERY}) + "\n")
        self.proc.stdin.flush()
        return parse(json.loads(self.proc.stdout.readline() or '{"error": "the worker died"}'))

    def close(self) -> None:
        try:
            self.proc.stdin.close()
            self.proc.wait(timeout=10)
        except Exception:
            self.proc.kill()


def by_frames(frames: list, loose: Callable) -> Dets:
    """A frame detector (MTCNN) on the same sampled frames the worker reads."""
    return {t: loose(frames[t]) for t in range(0, len(frames), EVERY)}


def queue_busy() -> bool:
    from studio import comfy
    try:
        return comfy.busy()
    except Exception:                       # an engine that answers wrong is not idle
        return True


class Finder:
    """take, frames -> boxes per sampled frame: the YOLO worker, else MTCNN (`loose`)."""

    def __init__(self, loose: Callable, route: Callable | None = None, start: Callable | None = None,
                 busy: Callable[[], bool] | None = None, claim: Callable | None = None):
        if route is None:
            from studio.compute_device import device_for as route
        if claim is None:
            from studio.compute_device import claim
        self.loose, self.route, self.busy, self.claim = loose, route, busy or queue_busy, claim
        self.start = start or (lambda device: Worker(spawn(device)))
        self.worker, self.device, self.broken, self.held = None, "", False, ExitStack()
        atexit.register(self.close)

    def __call__(self, take: Path, frames: list) -> Dets:
        if not self.broken:
            try:
                return self.ready()(take)
            except Exception as failed:
                print(f"FACE DETECT -> mtcnn: the YOLO worker failed ({failed}); MTCNN reads the rest", flush=True)
                self.broken = True
                self.close()
        return by_frames(frames, self.loose)

    def ready(self):
        """The live worker; a GPU one that sees a render arrive is swapped for a CPU one, and one
        that idled out between two takes is started again (never handed to MTCNN for that)."""
        if self.worker is not None and self.worker.exited():
            print("FACE DETECT: the worker idled out between takes; started again", flush=True)
            self.close()
        if self.worker is not None and self.device == "cuda" and self.busy():
            print("DEVICE face detect -> cpu: a render arrived", flush=True)
            self.close()
            self.open("cpu")
        if self.worker is None:
            self.open(self.route("face detect", YOLO_GB))
        return self.worker

    def open(self, device: str) -> None:
        if device == "cuda":
            self.held.enter_context(self.claim("face detect worker"))
        self.worker, self.device = self.start(device), device

    def close(self) -> None:
        if self.worker is not None:
            self.worker.close()
            self.worker = None
        self.held.close()
