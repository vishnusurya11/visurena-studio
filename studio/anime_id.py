"""The face refine's anime identity terms, routed like its detector (studio/face_detect.py): a
worker under ComfyUI's embedded python (studio/anime_id_worker.py) reads CCIP and clip_vision_h
for the sheet's face against the take's crops and the refined ones.  Facenet is a photo model:
it read ep01 T01 Utterson at 0.04 on his own take (docs/audit/2026-10-19_face_blur/bench), so a
cel face needs a term trained on drawn characters.  A worker that fails an ask (its 120 s idle
exit races the request) is started afresh once; one that will not start or fails again leaves
the terms unread (None) for that crop and every later one, said in the log; the gate then reads
facenet alone, as before.
"""
from __future__ import annotations

import atexit
import json
import os
import subprocess
import tempfile
from contextlib import ExitStack
from pathlib import Path
from typing import Callable

import numpy as np

from studio.face_detect import queue_busy, worker_env

THREADS = 4
ID_GB = 3.5
"""clip_vision_h in float32 (2.5 GB) and CCIP's caformer, with room."""
SAME_CHARACTER = 0.17847511429108218
"""metrics.json of ccip-caformer-24-randaug-pruned: a CCIP distance under this is the same character."""
CCIP_DIR = Path("ComfyUI") / "models" / "ccip" / "ccip-caformer-24-randaug-pruned"
CLIP_H = Path("ComfyUI") / "models" / "clip_vision" / "clip_vision_h.safetensors"


def worker_argv(python: Path, root: Path, device: str) -> list[str]:
    return [str(python), "-I", str(Path(__file__).with_name("anime_id_worker.py")), str(Path(root) / CCIP_DIR),
            str(Path(root) / CLIP_H), device, str(THREADS)]


def spawn(device: str) -> subprocess.Popen:
    from studio import master_upscale
    from studio.engine_ops import portable_root
    python = master_upscale.av3_paths()[0]
    return subprocess.Popen(worker_argv(python, portable_root(os.environ), device), stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, text=True, encoding="utf-8", env=worker_env(device))


def parse(said: dict) -> tuple[np.ndarray, np.ndarray]:
    """(CCIP distance matrix, clip cosine matrix); an error answer raises."""
    if "ccip" not in said:
        raise RuntimeError(said.get("error", "no answer"))
    return np.array(said["ccip"], float), np.array(said["clip"], float)


def terms(ccip: np.ndarray, clip: np.ndarray, n_src: int) -> dict:
    """Row 0 is the sheet, rows 1..n_src the take's crops, the rest the refined crops: the mean
    CCIP distance and clip cosine of the sheet to each side."""
    src, ref = slice(1, 1 + n_src), slice(1 + n_src, None)
    return {"ccip_src": float(np.mean(ccip[0, src])), "ccip_ref": float(np.mean(ccip[0, ref])),
            "clip_src": float(np.mean(clip[0, src])), "clip_ref": float(np.mean(clip[0, ref]))}


class Worker:
    """One started worker process, asked one list of pictures at a time."""

    def __init__(self, proc):
        self.proc = proc
        if json.loads(proc.stdout.readline() or "{}").get("ready") is not True:
            self.close()
            raise RuntimeError("the anime identity worker never said ready")

    def exited(self) -> bool:
        return self.proc.poll() is not None

    def __call__(self, paths: list) -> tuple[np.ndarray, np.ndarray]:
        if (gone := self.proc.poll()) is not None:
            raise RuntimeError(f"the anime identity worker had exited (code {gone})")
        self.proc.stdin.write(json.dumps({"images": [str(p) for p in paths]}) + "\n")
        self.proc.stdin.flush()
        return parse(json.loads(self.proc.stdout.readline() or '{"error": "the worker died"}'))

    def close(self) -> None:
        try:
            self.proc.stdin.close()
            self.proc.wait(timeout=10)
        except Exception:
            self.proc.kill()


def write_crops(folder: Path, sheet: np.ndarray, src: list, ref: list) -> list[Path]:
    """sheet.png, src<k>.png, ref<k>.png in `folder`, in the order the terms read them."""
    from PIL import Image
    named = [("sheet", sheet)] + [(f"src{k}", c) for k, c in enumerate(src)] + [(f"ref{k}", c) for k, c in enumerate(ref)]
    out = []
    for name, rgb in named:
        Image.fromarray(np.ascontiguousarray(rgb)).save(folder / f"{name}.png")
        out.append(folder / f"{name}.png")
    return out


class Reader:
    """sheet crop, take crops, refined crops -> the four terms, or None unread."""

    def __init__(self, route: Callable | None = None, start: Callable | None = None,
                 busy: Callable[[], bool] | None = None, claim: Callable | None = None):
        if route is None:
            from studio.compute_device import device_for as route
        if claim is None:
            from studio.compute_device import claim
        self.route, self.busy, self.claim = route, busy or queue_busy, claim
        self.start = start or (lambda device: Worker(spawn(device)))
        self.worker, self.device, self.broken, self.held = None, "", False, ExitStack()
        atexit.register(self.close)

    def __call__(self, sheet, src: list, ref: list) -> dict | None:
        if sheet is None or self.broken or not src or not ref:
            return None
        try:
            with tempfile.TemporaryDirectory() as folder:
                ccip, clip = self.ask(write_crops(Path(folder), sheet, src, ref))
            return {k: round(v, 4) for k, v in terms(ccip, clip, len(src)).items()}
        except Exception as failed:
            print(f"ANIME ID -> unread: the worker failed ({failed}); facenet alone reads identity", flush=True)
            self.broken = True
            self.close()
            return None

    def ask(self, paths: list[Path]) -> tuple[np.ndarray, np.ndarray]:
        """One ask; a worker that failed it is started afresh ONCE and asked again.  Its 120 s idle
        exit races the next request (BENCH_R2 finding 1: ep01 T13 read "the worker died" after a
        136 s render), so one fresh 12.8 s load answers it; a second failure raises."""
        try:
            return self.ready()(paths)
        except Exception as died:
            print(f"ANIME ID -> restart: {died}; one fresh worker", flush=True)
            self.close()
            return self.ready()(paths)

    def ready(self):
        """The live worker; a GPU one that sees a render arrive is swapped for a CPU one."""
        if self.worker is not None and self.worker.exited():
            self.close()
        if self.worker is not None and self.device == "cuda" and self.busy():
            print("DEVICE anime id -> cpu: a render arrived", flush=True)
            self.close()
            self.open("cpu")
        if self.worker is None:
            self.open(self.route("anime id", ID_GB))
        return self.worker

    def open(self, device: str) -> None:
        if device == "cuda":
            self.held.enter_context(self.claim("anime id worker"))
        self.worker, self.device = self.start(device), device

    def close(self) -> None:
        if self.worker is not None:
            self.worker.close()
            self.worker = None
        self.held.close()
