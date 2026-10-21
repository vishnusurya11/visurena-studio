"""The fake workers' shared protocol (2026-10-21_ep02_proof 2.3, R10, R11, F17).

Each fake speaks its real worker's stdin/stdout JSON line protocol (studio/face_detect_worker,
studio/anime_id_worker, studio/whisper_worker): `{"ready": true}` once, then one answer line per
asked line, exiting on EOF or after `idle` seconds without one.  It answers from a memo keyed by
the asked file's BYTES (a take for the detector, the pictures in order for anime id, a wav for
whisper), filled by the REAL workers on the CPU (scripts/proof/fill_memos.py).  A miss is
`canned` and refuses: an empty detection, an error for an identity ask (the terms stay unread),
an EMPTY transcript (never the requested text).  On ask number `die_at` (1-based, 0 = never) it
exits without answering.  Every answer, death and exit is a row in the log file it is given.

    python studio/rehearsal/workers/fake_<kind>_worker.py <memo.json> <die_at> <idle_s> <log.jsonl>

Stdlib only: a worker never needs the studio's imports to answer."""
from __future__ import annotations

import hashlib
import json
import os
import queue
import sys
import threading
import time
from pathlib import Path
from typing import Callable

DIED = 3
"""The exit code of a worker told to die on a line (F17)."""
CANNED_ID = "canned: no memo for this identity ask (rehearsal)"


def file_key(path) -> str | None:
    """sha256 of the file's bytes; None when it cannot be read."""
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    except OSError:
        return None


def detect_key(path, every: int) -> str | None:
    key = file_key(path)
    return f"{key}:{int(every)}" if key else None


def images_key(paths) -> str | None:
    """One key for the pictures IN ORDER (the terms read row 0 as the sheet)."""
    keys = [file_key(p) for p in paths]
    return hashlib.sha256("\n".join(keys).encode("ascii")).hexdigest() if all(keys) else None


def read_memo(path) -> dict:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def answer_detect(ask: dict, memo: dict) -> tuple[dict, str, str | None]:
    key = detect_key(ask.get("video", ""), ask.get("every", 3))
    return ({"dets": memo[key]}, "exact", key) if key in memo else ({"dets": {}}, "canned", key)


def answer_anime(ask: dict, memo: dict) -> tuple[dict, str, str | None]:
    key = images_key(ask.get("images") or [])
    return (dict(memo[key]), "exact", key) if key in memo else ({"error": CANNED_ID}, "canned", key)


def answer_whisper(ask: dict, memo: dict) -> tuple[dict, str, str | None]:
    key = file_key(ask.get("clip", ""))
    return ({"text": memo[key]}, "exact", key) if key in memo else ({"text": ""}, "canned", key)


def lines(source, idle: float | None):
    """The source's lines, ending at EOF; queue.Empty after `idle` seconds without one."""
    got: queue.Queue = queue.Queue()
    threading.Thread(target=lambda: [got.put(x) for x in source] + [got.put(None)], daemon=True).start()
    while (line := got.get(timeout=idle)) is not None:
        yield line


def log(path, row: dict) -> None:
    with open(path, "a", encoding="utf-8") as out:
        out.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "pid": os.getpid(), **row}) + "\n")


def answer_lines(kind: str, answer: Callable, memo: dict, die_at: int, idle: float, logged: Callable,
                 source, sink) -> str:
    """Answer every asked line; the reason the loop ended (eof, idle or died)."""
    n = 0
    try:
        for line in lines(source, idle):
            if not line.strip():
                continue
            n += 1
            if n == die_at:
                logged({"worker": kind, "event": "died", "line": n})
                return "died"
            said, label, key = answer(json.loads(line), memo)
            logged({"worker": kind, "event": "answer", "line": n, "label": label, "key": key})
            sink.write(json.dumps(said) + "\n")
            sink.flush()
    except queue.Empty:
        return "idle"
    return "eof"


def serve(kind: str, answer: Callable, argv: list[str], source=None, sink=None) -> int:
    """The worker's main: ready, the lines, then its exit code (DIED when told to die)."""
    memo_path, die_at, idle, log_path = argv[0], int(argv[1]), float(argv[2]), argv[3]
    source, sink = source or sys.stdin, sink or sys.stdout
    sink.write(json.dumps({"ready": True}) + "\n")
    sink.flush()
    ended = answer_lines(kind, answer, read_memo(memo_path), die_at, idle or None,
                         lambda row: log(log_path, row), source, sink)
    log(log_path, {"worker": kind, "event": "exit", "why": ended})
    return DIED if ended == "died" else 0
