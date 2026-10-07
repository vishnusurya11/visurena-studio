"""Engine operations for the autopilot: the memory recipes as code.

Decision 2026-10-06 (the autopilot, ops §2's survival matrix): a hung engine
is a run whose log is quiet past twice the step's budget while /queue shows
the same prompt; the cure is kill the run TREE, kill ComfyUI, relaunch it,
wait for /system_stats, relaunch the drive.  Two lessons make this a module
and not a shell line: Stop-Process on uv.exe alone leaves the python children
rendering (2026-09-05, run 12c's orphan rendered takes 50 min after its uv
died), and a VRAM-full engine ignores /interrupt and the queue clear
(2026-09-06, run 18 lost 11 h to one hung read).  Every I/O is an injected
callable; the portable root is ONE constant behind one env var, and nothing
here writes a path anywhere.
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import time
import urllib.request
from pathlib import Path
from typing import Callable, Iterable

from studio.command_center.procs import ProcInfo
from studio.comfy import HOST

ENV_PORTABLE = "COMFY_PORTABLE"
DEFAULT_PORTABLE = "D:/Projects/KingdomOfViSuReNa/alpha/ComfyUI_windows_portable"
"""The portable ComfyUI's folder on this box; `COMFY_PORTABLE` overrides it."""
ENGINE_ARGS = ("-s", "ComfyUI/main.py", "--windows-standalone-build", "--reserve-vram", "2")
"""The launch the owner's hand used on 2026-09-06, verbatim (memory comfy-restart)."""
ENGINE_MARK = "ComfyUI/main.py"
RUN_MARKS = ("drive.py", "episode.py", "scripts/episode/")
"""A command line running this episode carries one of these and the codex + number."""
READY_SECONDS = 600.0
"""Custom nodes load in 1-2 min; comfy.RESTART_SECONDS is the same patience."""
READY_POLL = 5.0


def _get_json(url: str, timeout: float = 5.0) -> dict:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.loads(response.read())


def alive(base_url: str = HOST, get: Callable[[str], dict] = _get_json) -> bool:
    """Whether the engine answers /system_stats now; anything else is a no."""
    try:
        return isinstance(get(f"{base_url}/system_stats"), dict)
    except Exception:                       # noqa: BLE001 -- down, refusing, or mid-restart: all "no"
        return False


def queue(base_url: str = HOST, get: Callable[[str], dict] = _get_json) -> dict:
    """{running_ids, pending} off /queue.  An engine that cannot be reached
    holds no queue (comfy.queue_counts' rule: a restart empties it)."""
    try:
        doc = get(f"{base_url}/queue")
    except Exception:                       # noqa: BLE001
        return {"running_ids": [], "pending": 0}
    running = [str(item[1]) for item in doc.get("queue_running", []) if len(item) > 1]
    return {"running_ids": running, "pending": len(doc.get("queue_pending", []))}


def same_prompt_stuck(before: dict, after: dict) -> bool:
    """The hung-engine signal: one prompt running at both ends of the window."""
    ids = list(before.get("running_ids") or [])
    return bool(ids) and ids == list(after.get("running_ids") or [])


def _slashed(cmdline: str) -> str:
    return cmdline.replace("\\", "/")


def run_tree(rows: Iterable[ProcInfo], codex: str, n: int) -> list[ProcInfo]:
    """Every process whose command line runs THIS episode: the drive, the
    runner, a step script, a step's own child -- uv, the venv shim and the
    interpreter all match, because the kill must reach the leaves."""
    wanted = {str(n), f"{n:02d}", f"ep{n:02d}"}
    hits = []
    for p in rows:
        line = _slashed(p.cmdline)
        if any(mark in line for mark in NEVER_KILL):
            continue                        # the supervisor or an operator's command, never a run
        if codex in line and any(mark in line for mark in RUN_MARKS) \
                and wanted & set(line.replace('"', " ").split()):
            hits.append(p)
    return hits


NEVER_KILL = ("autopilot.py",)
"""A command line the kill never touches: 2026-10-07 `kill_run_tree(... 22)`
matched the shell running `autopilot.py retry 22 --book 2026...` (codex, number
and 'scripts/episode/' all present) and killed the operator's own command."""


def drive_alive(rows: Iterable[ProcInfo], codex: str, n: int) -> bool:
    """This episode's drive.py runs: the supervisor's liveness question, asked
    of the run tree so its own line never answers it (2026-10-07 14:06: the
    process table's find_drive grew a book-wide fallback and handed the
    autopilot its own pid; ep19 read "drive alive" and waited on itself)."""
    return any("drive.py" in _slashed(p.cmdline) for p in run_tree(rows, codex, n))


def _terminate(pid: int) -> None:
    try:
        os.kill(pid, signal.SIGTERM)        # TerminateProcess on Windows
    except OSError:
        pass                                # already gone


def kill_run_tree(rows: Iterable[ProcInfo], codex: str, n: int, kill: Callable[[int], None] = _terminate,
                  keep: Iterable[int] | None = None) -> list[int]:
    """Kill the whole tree of this episode's run, never the caller's own pid;
    the pids killed, in table order."""
    spared = set(keep) if keep is not None else {os.getpid()}
    pids = [p.pid for p in run_tree(rows, codex, n) if p.pid not in spared]
    for pid in pids:
        kill(pid)
    return pids


def engine_rows(rows: Iterable[ProcInfo]) -> list[ProcInfo]:
    """The ComfyUI process(es): found by command line, as the hand did."""
    return [p for p in rows if ENGINE_MARK in _slashed(p.cmdline)]


def kill_engine(rows: Iterable[ProcInfo], kill: Callable[[int], None] = _terminate) -> list[int]:
    """Kill ComfyUI's main.py; the pids killed."""
    pids = [p.pid for p in engine_rows(rows)]
    for pid in pids:
        kill(pid)
    return pids


def portable_root(env: dict | os._Environ = os.environ) -> Path:
    """The portable folder: `COMFY_PORTABLE`, else the one default."""
    return Path(env.get(ENV_PORTABLE) or DEFAULT_PORTABLE)


def engine_command(root: Path | str | None = None) -> tuple[list[str], Path]:
    """(argv, cwd) for the engine: the embedded python, from the portable folder."""
    root = Path(root) if root else portable_root()
    return [str(root / "python_embeded" / "python.exe"), *ENGINE_ARGS], root


def _launch(cmd: list[str], cwd: Path) -> None:
    """Detached, so the engine outlives the supervisor that started it."""
    flags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) | getattr(subprocess, "DETACHED_PROCESS", 0)
    subprocess.Popen(cmd, cwd=str(cwd), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                     creationflags=flags)


def wait_alive(base_url: str = HOST, seconds: float = READY_SECONDS, poll: float = READY_POLL,
               now: Callable[[], float] = time.time, sleep: Callable[[float], None] = time.sleep,
               probe: Callable[[str], bool] | None = None) -> bool:
    """Poll until /system_stats answers or the patience runs out."""
    up = probe or (lambda url: alive(url))
    give_up = now() + seconds
    while True:
        if up(base_url):
            return True
        if now() >= give_up:
            return False
        sleep(poll)


def restart(launch: Callable[[list[str], Path], None] = _launch, wait: Callable[[], bool] = wait_alive,
            root: Path | str | None = None) -> bool:
    """Relaunch the engine from its folder and wait for it; True when it answers."""
    cmd, cwd = engine_command(root)
    launch(cmd, cwd)
    return wait()
