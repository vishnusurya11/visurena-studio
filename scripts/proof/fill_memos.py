"""Fill the fake workers' memos with the REAL workers' readings, on the CPU (2026-10-21_ep02_proof
2.3, R10, R11).

    uv run --no-sync python scripts/proof/fill_memos.py <memo_dir> [--whisper W.wav ...]
        [--detect T01.mp4 ...] [--anime <ask folder> ...]

whisper  the CPU ear (voice_qc.transcriber on "cpu": large-v3-turbo fp32) over each wav
detect   face_detect's YOLO worker started on "cpu" over each take, every face_track.EVERY frames
anime    anime_id's worker started on "cpu" over each ask folder (sheet.png, src<k>.png, ref<k>.png)
Each reading lands in <memo_dir>/<kind>.json under the key the fake worker looks up
(studio/rehearsal/workers: the bytes' sha256); a key already there is kept, never re-read.

CPU only (CUDA_VISIBLE_DEVICES="", YOLO_OFFLINE=1), and only while ComfyUI is idle: a running or
queued render refuses the fill (owner 2026-10-18).  Free and local, so its real-model test is
`@pytest.mark.local`, never in the default run.  Run it OUTSIDE a rehearsal (VISURENA_LIBRARY
unset): the real workers run under the portable python, which the fence refuses.  The seconds
each kind took are printed: that is the memo-fill time DESIGN section 9 asks to be measured."""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Callable, Iterable

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from studio.rehearsal.workers import detect_key, file_key, images_key, read_memo  # noqa: E402


class EngineBusy(RuntimeError):
    """ComfyUI has a render running or queued: the fill waits for it."""


def cpu_env(env=None) -> dict:
    """The environment a real worker reads on the CPU with: no card, nothing phones home."""
    return dict(os.environ if env is None else env) | {"CUDA_VISIBLE_DEVICES": "", "YOLO_OFFLINE": "1"}


def engine_idle(fetch: Callable[[], tuple[int, int]] | None = None) -> bool:
    """True when the queue is empty or no engine answers at all; a garbled answer is not idle."""
    if fetch is None:
        from studio import comfy
        fetch = comfy.queue_counts_strict
    try:
        running, pending = fetch()
    except OSError:                                 # refused / unreachable: nothing renders
        return True
    except Exception:                               # noqa: BLE001 -- an engine that answers wrong is busy
        return False
    return running + pending == 0


def detect_every() -> int:
    from studio.face_track import EVERY
    return EVERY


def ask_pictures(folder: Path) -> list[Path]:
    """An anime ask folder's pictures in the order anime_id.write_crops stages them."""
    def order(p: Path) -> tuple[int, int]:
        rank = {"sheet": 0, "src": 1, "ref": 2}
        head = p.stem.rstrip("0123456789")
        return rank.get(head, 3), int(p.stem[len(head):] or 0)
    return sorted(Path(folder).glob("*.png"), key=order)


def fill_kind(memo: Path, items: Iterable, key_of: Callable, read: Callable) -> dict:
    """Read every item whose key the memo lacks; the counts and the seconds it took.  The memo is
    written after each reading, so a worker that dies mid-fill loses only the item it died on."""
    have, began, filled, kept = read_memo(memo), time.monotonic(), 0, 0
    memo.parent.mkdir(parents=True, exist_ok=True)
    for item in items:
        key = key_of(item)
        if key is None or key in have:
            kept += 1
            continue
        have[key] = read(item)
        filled += 1
        memo.write_text(json.dumps(have, indent=1), encoding="utf-8")
    memo.write_text(json.dumps(have, indent=1), encoding="utf-8")
    return {"filled": filled, "kept": kept, "seconds": round(time.monotonic() - began, 2)}


def real_ear() -> Callable[[Path], str]:
    os.environ.update(cpu_env())
    from studio import voice_qc
    return voice_qc.transcriber(device="cpu")


@contextmanager
def real_worker(kind: str):
    """The REAL detect or anime worker started on the CPU, closed after the fill."""
    os.environ.update(cpu_env())
    from studio import anime_id, face_detect
    worker = face_detect.Worker(face_detect.spawn("cpu")) if kind == "detect" else anime_id.Worker(anime_id.spawn("cpu"))
    try:
        yield worker
    finally:
        worker.close()


def detect_reader(worker) -> Callable[[Path], dict]:
    return lambda take: {str(t): found for t, found in worker(Path(take)).items()}


def anime_reader(worker) -> Callable[[Path], dict]:
    def read(folder: Path) -> dict:
        ccip, clip = worker(ask_pictures(folder))
        return {"ccip": ccip.tolist(), "clip": clip.tolist()}
    return read


def fill_detect(memo: Path, takes: list, see: Callable | None) -> dict:
    every = detect_every()
    if see is not None:
        return fill_kind(memo, takes, lambda t: detect_key(t, every), see)
    with real_worker("detect") as worker:
        return fill_kind(memo, takes, lambda t: detect_key(t, every), detect_reader(worker))


def fill_anime(memo: Path, asks: list, identify: Callable | None) -> dict:
    key = lambda folder: images_key(ask_pictures(folder))  # noqa: E731
    if identify is not None:
        return fill_kind(memo, asks, key, identify)
    with real_worker("anime") as worker:
        return fill_kind(memo, asks, key, anime_reader(worker))


def fill(memo_dir: Path, whisper=(), detect=(), anime=(), hear: Callable | None = None, see: Callable | None = None,
         identify: Callable | None = None, idle: Callable[[], bool] = engine_idle) -> dict:
    """Fill each named kind's memo; refuses while ComfyUI has work."""
    if not idle():
        raise EngineBusy("ComfyUI has a render running or queued; fill the memos when it is idle")
    memo_dir, got = Path(memo_dir), {}
    if whisper:
        got["whisper"] = fill_kind(memo_dir / "whisper.json", list(whisper), file_key, hear or real_ear())
    if detect:
        got["detect"] = fill_detect(memo_dir / "detect.json", list(detect), see)
    if anime:
        got["anime"] = fill_anime(memo_dir / "anime.json", list(anime), identify)
    return got


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("memo_dir")
    for kind in ("whisper", "detect", "anime"):
        p.add_argument(f"--{kind}", nargs="*", default=[])
    args = p.parse_args(argv)
    got = fill(Path(args.memo_dir), [Path(w) for w in args.whisper], [Path(t) for t in args.detect],
               [Path(a) for a in args.anime], hear=real_ear() if args.whisper else None, idle=engine_idle)
    for kind, counts in got.items():
        print(f"{kind}: {counts['filled']} filled, {counts['kept']} kept, {counts['seconds']} s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
