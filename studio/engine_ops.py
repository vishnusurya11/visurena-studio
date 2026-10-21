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

from studio import settings
from studio.command_center.procs import ProcInfo
from studio.comfy import HOST

ENV_PORTABLE = "COMFY_PORTABLE"
DEFAULT_PORTABLE = settings.comfy_portable("D:/Projects/KingdomOfViSuReNa/alpha/ComfyUI_windows_portable")
"""The portable ComfyUI's folder on this box; `COMFY_PORTABLE` overrides it.  In a rehearsal
it is a sandbox path that holds no engine (2026-10-21_ep02_proof 1.2)."""
ENGINE_ARGS = ("-s", "ComfyUI/main.py", "--windows-standalone-build",
               "--disable-assets", "--reserve-vram", "2")
"""The launch the owner's hand used on 2026-09-06 (memory comfy-restart), plus
`--disable-assets` since v0.41.2: the standalone build switches the assets system on,
and its background scan stats every file under models/input/output on the D: HDD,
holding the disk at 100 % for minutes after each start (owner, 2026-10-17)."""
ENGINE_MARK = "ComfyUI/main.py"
RUN_MARKS = ("drive.py", "episode.py", "scripts/episode/")
"""A command line running this episode carries one of these and the codex + number."""
READY_SECONDS = 600.0
"""comfy.RESTART_SECONDS is the same patience.  Measured 2026-10-21 (CRASH.md): a start took
333, 386 and 775 s to answer /system_stats on this box (custom-node imports on the D: HDD), so
600 s is about the median, not a bound.  A False after it launches nothing: the next tick's
restart() finds the starting engine in the table and waits on it."""
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


def _memory_status() -> dict:
    """GlobalMemoryStatusEx as a dict (Windows); {} where the call is not there."""
    import ctypes

    class Status(ctypes.Structure):
        _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
    status = Status()
    status.dwLength = ctypes.sizeof(Status)
    try:
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status))
    except (AttributeError, OSError):
        return {}
    return {name: getattr(status, name) for name, _ in Status._fields_}


def commit_free_gb(stat: Callable[[], dict] = _memory_status) -> float | None:
    """Host commit headroom in GB (ullAvailPageFile): ComfyUI's 'error 1450' came
    with 0.8 GB left while RAM looked free (Jekyll ep01, cured by POST /free)."""
    avail = stat().get("ullAvailPageFile")
    return None if avail is None else round(avail / 2**30, 2)


def _post_json(url: str, body: dict, timeout: float = 30.0) -> bool:
    request = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                     headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout):
        return True


def free(base_url: str = HOST, post: Callable[[str, dict], bool] = _post_json) -> bool:
    """POST /free: unload models and free memory without touching the queue."""
    try:
        return bool(post(f"{base_url}/free", {"unload_models": True, "free_memory": True}))
    except Exception:                       # noqa: BLE001 -- an engine that will not answer was not freed
        return False


def log_tail(n: int = 3, root: Path | str | None = None) -> list[str]:
    """The engine log's last n lines (ComfyUI/user/comfyui.log); none when absent."""
    path = (Path(root) if root else portable_root()) / "ComfyUI" / "user" / "comfyui.log"
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    return [ln.strip() for ln in lines if ln.strip()][-n:]


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


def _cpu_seconds(pid: int) -> float:
    """User + kernel CPU seconds a process has used (GetProcessTimes); 0 when it is gone."""
    import ctypes
    from ctypes import wintypes
    handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)           # QUERY_LIMITED_INFORMATION
    if not handle:
        return 0.0
    times = [wintypes.FILETIME() for _ in range(4)]
    ok = ctypes.windll.kernel32.GetProcessTimes(handle, *[ctypes.byref(t) for t in times])
    ctypes.windll.kernel32.CloseHandle(handle)
    ticks = lambda t: (t.dwHighDateTime << 32 | t.dwLowDateTime)
    return (ticks(times[2]) + ticks(times[3])) / 1e7 if ok else 0.0


def tree_cpu_s(rows: Iterable[ProcInfo], codex: str, n: int, cpu: Callable[[int], float] = _cpu_seconds) -> float:
    """CPU seconds burned by this episode's whole run tree: the liveness the log cannot give."""
    return round(sum(cpu(p.pid) for p in run_tree(rows, codex, n)), 2)


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


def _live_rows() -> list[ProcInfo]:
    """The process table walked NOW: the caller's kill a moment ago made any cached one stale
    (2026-10-21 crash cycle 4: a cached dead main.py cost 605.7 s of waiting on nothing)."""
    from studio.command_center.procs import list_processes
    return list_processes(fresh=True)


def newcomers(before: Iterable[ProcInfo], now: Iterable[ProcInfo]) -> list[ProcInfo]:
    """The engine rows of `now` that `before` did not hold: another restart's launch."""
    seen = {p.pid for p in before}
    return [p for p in engine_rows(now) if p.pid not in seen]


def restart(launch: Callable[[list[str], Path], None] = _launch, wait: Callable[[], bool] = wait_alive,
            root: Path | str | None = None, rows: Callable[[], list[ProcInfo]] = _live_rows,
            kill: Callable[[int], None] = _terminate) -> bool:
    """An engine process already starting is waited on, never stacked (2026-10-18: three
    main.py on one HDD); one that never answers is killed, the table is read AGAIN, and an
    engine someone launched meanwhile is waited on (2026-10-21 cycle 4: a peer's restart and
    this one each launched one); only then is ONE launch made and waited on."""
    if (live := engine_rows(rows())) and wait():
        return True
    kill_engine(live, kill)
    if newcomers(live, rows()):
        return wait()
    cmd, cwd = engine_command(root)
    launch(cmd, cwd)
    return wait()
