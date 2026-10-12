"""The GPU card's look at the local ComfyUI (board review 2026-10-12, 02 #4): the
card said "GPU idle" while the engine ran a prompt for a script outside the runner.

Read-only: one GET of /queue with a short timeout, cached for TTL_S, refreshed on
a background thread so a page or a pulse answers from the last snapshot at once
and never waits on the engine.  The holder is named from the process table the
board already reads (procs.list_processes); nothing here spawns or posts."""
from __future__ import annotations

import json
import re
import threading
import time
import urllib.request
from typing import Callable

from studio.comfy import HOST

TTL_S = 5.0
TIMEOUT_S = 0.5
DOWN = {"up": False, "running": [], "pending": 0}
CODEX_IN = re.compile(r"\b(\d{14})\b")
SCRIPT_IN = re.compile(r"scripts[\\/]([\w./\\-]+\.py)")


def fetch_queue(timeout: float = TIMEOUT_S) -> dict:
    """GET /queue from the local engine (raises when it does not answer)."""
    with urllib.request.urlopen(f"{HOST}/queue", timeout=timeout) as response:
        return json.loads(response.read())


def parse(doc: dict) -> dict:
    """/queue as a snapshot: the running prompts' numbers and how many wait."""
    running = [item[0] for item in doc.get("queue_running") or [] if item]
    return {"up": True, "running": running, "pending": len(doc.get("queue_pending") or [])}


def spawn_thread(fn: Callable[[], None]) -> None:
    threading.Thread(target=fn, name="comfy-tap", daemon=True).start()


class Tap:
    """The last /queue snapshot, refreshed off the caller's thread when older than the TTL."""

    def __init__(self, fetch: Callable[[], dict] | None = None, ttl: float = TTL_S,
                 clock: Callable[[], float] = time.monotonic, spawn: Callable = spawn_thread):
        self.fetch = fetch or (lambda: fetch_queue())      # late-bound: the test trap replaces fetch_queue
        self.ttl, self.clock, self.spawn = ttl, clock, spawn
        self.snap, self.stamp, self.busy, self.lock = dict(DOWN), float("-inf"), False, threading.Lock()

    def read(self) -> dict:
        """The snapshot now; a refresh starts when it is stale and none is in flight."""
        with self.lock:
            due = not self.busy and self.clock() - self.stamp >= self.ttl
            self.busy = self.busy or due
        if due:
            self.spawn(self.refresh)
        return dict(self.snap)

    def refresh(self) -> None:
        """One fetch; an engine that does not answer reads DOWN."""
        try:
            snap = parse(self.fetch())
        except Exception:                   # noqa: BLE001 -- down, refusing, timing out: all DOWN
            snap = dict(DOWN)
        with self.lock:
            self.snap, self.stamp, self.busy = snap, self.clock(), False


def holder(rows: list, names: dict[str, str]) -> str:
    """`refs/looks_table.py · Jekyll`: the newest script under scripts/ whose command
    line names a book -- the likeliest owner of the engine's prompt; '' when none."""
    hits = [(p.started or 0.0, m.group(1), c.group(1)) for p in rows
            if (m := SCRIPT_IN.search(p.cmdline)) and (c := CODEX_IN.search(p.cmdline))]
    if not hits:
        return ""
    _, script, codex = max(hits)
    return f"{script.replace(chr(92), '/')} · {names.get(codex, codex)}"


def engine_block(snap: dict, rows: list, names: dict[str, str]) -> dict | None:
    """What the GPU card adds: busy, the counts and who; None while the engine is down."""
    if not snap.get("up"):
        return None
    busy = bool(snap["running"])
    return {"busy": busy, "running": len(snap["running"]), "pending": snap["pending"],
            "who": holder(rows, names) if busy else ""}
