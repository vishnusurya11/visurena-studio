"""The recovery trace and the write sites (2026-10-21_ep02_proof DESIGN 3.3, R13, R14).

A sweep's point counts toward n only when its RECOVERY TRACE is distinct: the set of executed
(file, line) pairs in the recovery modules, captured with `sys.monitoring` LINE events in every
rehearsal process (activate.load_trace calls `install`).  Each location reports once and is then
DISABLEd, so a traced process pays one callback per distinct line.  Each process dumps its set to
`<sandbox>/traces/<pid>.json` at exit; a point's trace is the union of its run's files.

`record_writes` (an unfaulted run only) adds an audit hook that names every write under the
sandbox library by its FILE KIND (book-relative, digits as #), its code SITE (the first frame
outside the rehearsal package) and the STEP the runner is in at that write (`current_step`: the
runner's own frame, since episode.py imports every step), to `<sandbox>/writes/<pid>.jsonl`: the
F2/F3 kill points.  A child's fault hook (faults.arm, a kill at write k) and S0a's between-steps
checkpoint stop (checkpoint_stop) are armed from here too, one entry point."""
from __future__ import annotations

import atexit
import hashlib
import json
import os
import re
import sys
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable, Iterator, Mapping

from studio import settings

RECOVERY = ("studio/comfy.py", "studio/take_ladder.py", "scripts/episode/drive.py", "scripts/episode/autopilot.py",
            "studio/step_caps.py", "studio/episode_drive.py", "studio/episode_home.py", "studio/run_budget.py",
            "studio/run_clock.py", "studio/episode_clock.py", "studio/autopilot.py")
"""The recovery code (3.3) and the resume readers: what decides how a fault is recovered."""
TOOL_IDS = (3, 4)
"""sys.monitoring tool ids no named tool claims (0 debugger, 1 coverage, 2 profiler, 5 optimizer)."""
TRACES, WRITES = "traces", "writes"
OWN = str(Path(__file__).resolve().parent)
_STATE: dict = {"tool": None, "hits": set(), "writes": [], "busy": threading.local()}


def rel(filename: str, root: Path = settings.REPO, files: Iterable[str] = RECOVERY) -> str | None:
    """The repo-relative posix name of a recovery module, else None."""
    try:
        name = Path(filename).resolve().relative_to(Path(root).resolve()).as_posix()
    except (ValueError, OSError):
        return None
    return name if name in set(files) else None


def callback(hits: set, root: Path, files: tuple[str, ...]):
    """The LINE callback: record a recovery line once, then DISABLE that location."""
    names: dict[str, str | None] = {}
    disable = sys.monitoring.DISABLE

    def on_line(code, line):
        name = names.get(code.co_filename, "?")
        if name == "?":
            name = names[code.co_filename] = rel(code.co_filename, root, files)
        if name is not None:
            hits.add((name, line))
        return disable
    return on_line


def start(hits: set, root: Path = settings.REPO, files: Iterable[str] = RECOVERY) -> int | None:
    """Claim a free tool id and turn LINE events on; None when every id is taken."""
    mon = sys.monitoring
    for tool in TOOL_IDS:
        if mon.get_tool(tool) is None:
            mon.use_tool_id(tool, "visurena-rehearsal-trace")
            mon.register_callback(tool, mon.events.LINE, callback(hits, Path(root), tuple(files)))
            mon.set_events(tool, mon.events.LINE)
            mon.restart_events()
            return tool
    return None


def stop(tool: int | None) -> None:
    if tool is not None:
        sys.monitoring.set_events(tool, 0)
        sys.monitoring.register_callback(tool, sys.monitoring.events.LINE, None)
        sys.monitoring.free_tool_id(tool)


@contextmanager
def capturing(root: Path = settings.REPO, files: Iterable[str] = RECOVERY) -> Iterator[set]:
    """The recovery lines executed inside the block."""
    hits: set = set()
    tool = start(hits, root, files)
    try:
        yield hits
    finally:
        stop(tool)


def signature(hits: Iterable[tuple[str, int]]) -> str:
    """The trace's identity: two points with the same executed lines are one sample."""
    text = "\n".join(f"{f}:{n}" for f, n in sorted(set(hits)))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def dump(folder: Path, name: str, hits: Iterable[tuple[str, int]]) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{name}.json"
    path.write_text(json.dumps(sorted([list(h) for h in set(hits)])), encoding="utf-8")
    return path


def read_all(folder: Path) -> set[tuple[str, int]]:
    """The union of every process's trace in a run's folder (a torn dump is skipped)."""
    out: set = set()
    for path in sorted(Path(folder).glob("*.json")) if Path(folder).is_dir() else []:
        try:
            out |= {(str(f), int(n)) for f, n in json.loads(path.read_text(encoding="utf-8"))}
        except (ValueError, TypeError):
            continue
    return out


# ---- write sites ---------------------------------------------------------------------

def kind_of(path, box: Path) -> str | None:
    """A write's file kind: its path under the sandbox book, each counter (2+ digits: T07, ep02)
    masked to '#'s, a name like r2v kept; None outside the sandbox library."""
    try:
        parts = Path(os.path.abspath(path)).relative_to(Path(os.path.abspath(box)) / settings.LIBRARY_DIR).parts
    except ValueError:
        return None
    masked = re.sub(r"\d{2,}", lambda m: "#" * len(m.group(0)), "/".join(parts[1:]))
    return masked if len(parts) > 1 else None


def site_of(frame) -> str:
    """The first frame outside this package and the standard library: `path:line`, repo-relative."""
    while frame is not None:
        name = frame.f_code.co_filename
        if not name.startswith(OWN) and "importlib" not in name and not name.startswith(sys.base_prefix):
            try:
                name = Path(name).resolve().relative_to(settings.REPO).as_posix()
            except (ValueError, OSError):
                pass
            return f"{name}:{frame.f_lineno}"
        frame = frame.f_back
    return "?"


def step_of(argv: list[str]) -> str:
    """The step a process runs ('09' for step_09_shoot.py), else its script's stem."""
    script = Path(argv[0]).name if argv else ""
    hit = re.match(r"step_(\d{2})_", script)
    return hit.group(1) if hit else (Path(script).stem or "?")


RUNNER = "studio/step_runner.py"
"""Where the episode runner's loop lives: episode.py IMPORTS every step (step_runner.import_step),
so the process is always episode.py and only the runner's frame knows which step is running."""


def runner_step(frame) -> str | None:
    """STEP_ID of the step the runner's `run_steps` frame holds, walking out from `frame`."""
    while frame is not None:
        code = frame.f_code
        if code.co_name == "run_steps" and Path(code.co_filename).as_posix().endswith(RUNNER):
            step = frame.f_locals.get("step")
            return str(step.STEP_ID) if hasattr(step, "STEP_ID") else None
        frame = frame.f_back
    return None


def current_step(frame=None) -> str:
    """The step the runner is in: this thread's run_steps frame, else the main thread's (a take
    worker), else the script's own name (a step run as its own process, or no runner at all)."""
    found = runner_step(frame or sys._getframe(1))
    if found is None and threading.current_thread() is not threading.main_thread():
        found = runner_step(sys._current_frames().get(threading.main_thread().ident))
    return found or step_of(sys.argv)


def writes_hook(box: Path):
    """An audit hook appending {kind, site, step} for every write-capable open in the sandbox library;
    the step is read at each write from the runner, never once from argv."""
    from studio.rehearsal import fence
    busy = _STATE["busy"]

    def hook(event: str, args: tuple) -> None:
        if event != "open" or getattr(busy, "on", False) or not fence.writes(args[1], args[2]):
            return
        busy.on = True
        try:
            if (kind := kind_of(args[0], box)) is not None:
                frame = sys._getframe(1)
                _STATE["writes"].append({"kind": kind, "site": site_of(frame), "step": current_step(frame)})
        finally:
            busy.on = False
    return hook


def flush(box: Path) -> None:
    """At exit: this process's trace and write rows into the sandbox."""
    _STATE["busy"].on = True
    name = str(os.getpid())
    if _STATE["tool"] is not None:
        dump(box / TRACES, name, _STATE["hits"])
    if rows := _STATE["writes"]:
        (box / WRITES).mkdir(parents=True, exist_ok=True)
        (box / WRITES / f"{name}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


def install(manifest: Mapping, box: Path | None = None) -> None:
    """Called by activate in every rehearsal process: trace (default on), write sites (opt in),
    the child's fault hook; everything lands under the sandbox at exit."""
    box = box or settings.sandbox()
    if box is None:                                    # a manifest handed in with no sandbox in the env (tests)
        return
    box = Path(box)
    if manifest.get("trace", True):
        _STATE["tool"] = start(_STATE["hits"])
    if manifest.get("record_writes"):
        sys.addaudithook(writes_hook(box))
    from studio.rehearsal import checkpoint_stop, faults
    faults.arm(manifest, box)
    checkpoint_stop.install(manifest, box)              # S0a: the runner stops in front of a due checkpoint
    atexit.register(flush, box)
