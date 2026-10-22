"""The face detect, anime id and whisper workers at the PROCESS boundary (2026-10-21_ep02_proof
2.3, R10, R11, F17).

Only each module's pure `worker_argv` is rebound, to
    [sys.executable, studio/rehearsal/workers/fake_<kind>_worker.py, <memo>, <die_at>, <idle_s>, <log>]
so the REAL spawn, Worker ready handshake, idle exit, routed_whisper's SPAWNS = 2 restart after a
death and anime_id's one fresh retry all run against a real child.  No `-I`: the fence refuses an
isolated Python child (it would skip the rehearsal boot and run unfenced), so the fake worker arms
its own fence like every other child.  `idle_s` is the real worker's IDLE_S over manifest.scale.

Two in-process reads at the same boundary are fed from the same memos: the VRAM read
(compute_device.smi_free_mb, nvidia-smi) answers the manifest's `vram_free_mb`, and the CPU ear
(voice_qc.transcriber, whisper in this process) hears the whisper memo, a miss an EMPTY text.

Manifest: `memos` (folder of detect.json, anime.json, whisper.json; default <sandbox>/memos),
`worker_die_at` {kind: line}, `vram_free_mb`, `scale`.  Rows go to <sandbox>/workers.jsonl."""
from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Callable, Mapping

from studio.rehearsal import fakes
from studio.rehearsal.workers import detect_key, file_key, heard, images_key, read_memo  # noqa: F401  (shared keys)

WORKERS = Path(__file__).resolve().with_name("workers")
KINDS = {"detect": ("studio.face_detect", "studio.face_detect_worker"),
         "anime": ("studio.anime_id", "studio.anime_id_worker"),
         "whisper": ("studio.routed_whisper", "studio.whisper_worker")}
"""kind -> (the client module whose worker_argv is rebound, the real worker holding IDLE_S)."""
VRAM_FREE_MB = 24 * 1024
"""The card's free MiB when the manifest names none: roomy, so the router's other reasons decide."""


def detect_every() -> int:
    from studio.face_track import EVERY
    return EVERY


def memo_path(manifest: Mapping, box: Path, kind: str) -> Path:
    return Path(manifest.get("memos") or Path(box) / "memos") / f"{kind}.json"


def idle_s(manifest: Mapping, kind: str) -> float:
    """The real worker's IDLE_S, divided by the rehearsal's time scale."""
    real = float(importlib.import_module(KINDS[kind][1]).IDLE_S)
    return real / float(manifest.get("scale") or 1)


def argv(kind: str, manifest: Mapping, box: Path) -> list[str]:
    die = int((manifest.get("worker_die_at") or {}).get(kind, 0))
    return [sys.executable, str(WORKERS / f"fake_{kind}_worker.py"), str(memo_path(manifest, box, kind)),
            str(die), str(idle_s(manifest, kind)), str(Path(box) / "workers.jsonl")]


def fake_argv(kind: str, manifest: Mapping, box: Path) -> Callable[..., list[str]]:
    """A worker_argv with the real signature's freedom: its arguments name the real worker's files."""
    return lambda *_args, **_kwargs: argv(kind, manifest, box)


def memo_ear(manifest: Mapping, box: Path) -> Callable[..., Callable[[Path], str]]:
    """voice_qc.transcriber's stand-in: the CPU ear hears the whisper memo, a miss nothing."""
    def transcriber(*_args, **_kwargs) -> Callable[[Path], str]:
        memo = read_memo(memo_path(manifest, box, "whisper"))

        def listen(clip: Path) -> str:
            text, label, key = heard(clip, memo)
            fakes.log(box, "workers", {"worker": "cpu_ear", "event": "answer", "label": label, "key": key})
            return text
        return listen
    return transcriber


def install(manifest: Mapping, box: Path) -> None:
    for kind, (client, _) in KINDS.items():
        fakes.rebind(client, "worker_argv", lambda _old, kind=kind: fake_argv(kind, manifest, box))
    free = int(manifest.get("vram_free_mb", VRAM_FREE_MB))
    fakes.rebind("studio.compute_device", "smi_free_mb", lambda _old: lambda *_a, **_k: free)
    fakes.rebind("studio.voice_qc", "transcriber", lambda _old: memo_ear(manifest, box))
