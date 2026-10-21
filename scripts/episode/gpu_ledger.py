#!/usr/bin/env python
"""The GPU/RAM ledger: a 5 s sampler that says where the machine's minutes went.

    uv run --no-sync python scripts/episode/gpu_ledger.py [--every 5] [--idle-exit 600]

Jekyll Kawajiri ep01 (retro 2026-10-19, package P13): the run lost hours that no
record could place -- ComfyUI died unseen, host commit sat at 0.8 GB, a GPU job
and its claim overlapped.  Every `--every` seconds one row goes to
library/.device/gpu_util.jsonl: the ComfyUI queue counts, the live device claims,
nvidia-smi's used MiB and util, the host's commit headroom and free RAM, and
ComfyUI's private bytes.  A probe that fails writes `probe_error` and the loop
goes on: a ledger that stops is the thing it was built to catch.

The autopilot starts it beside a drive.  `minutes_per_step` and `time_line` are
what the finish report reads: busy / claimed / idle minutes per step, and the
'charged | wall | dead' line (run_clock.dead_gaps, contract K4).  Every probe is
a `Probes` field, so the tests reach no GPU, no engine and no process table.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from studio import settings  # noqa: E402

LEDGER = settings.library_root() / ".device" / "gpu_util.jsonl"
LOCK = settings.library_root() / ".autopilot" / "gpu.lock"
EVERY_S = 5.0
BUSY_UTIL = 5
"""A GPU at or above this util % counts as busy even when /queue shows nothing."""


@dataclass
class Probes:
    """Every outward read the sampler makes; each returns plain data or raises."""
    queue: Callable[[], dict]                # {"running": n, "pending": n}
    claims: Callable[[], list]               # live device claims
    smi: Callable[[], dict]                  # {"gpu_used_mib", "gpu_util"}
    host: Callable[[], dict]                 # {"commit_free_gb", "ram_free_gb"}
    comfy_bytes: Callable[[], int | None]    # ComfyUI's private bytes


def _try(name: str, call: Callable[[], object], row: dict) -> object | None:
    """A probe's value, or None with its name appended to row['probe_error']."""
    try:
        return call()
    except Exception:                        # noqa: BLE001 -- a failed probe is a row, never a stop
        row.setdefault("probe_error", []).append(name)
        return None


def sample(probes: Probes, now: float) -> dict:
    """One ledger row; fields of a failed probe are absent and named in probe_error."""
    row: dict = {"ts": now}
    queue = _try("queue", probes.queue, row)
    if queue is not None:
        row.update(queue_running=queue.get("running", 0), queue_pending=queue.get("pending", 0))
    claims = _try("claims", probes.claims, row)
    if claims is not None:
        row["claims"] = len(claims)
    for name, call in (("smi", probes.smi), ("host", probes.host)):
        row.update(_try(name, call, row) or {})
    size = _try("comfy_bytes", probes.comfy_bytes, row)
    if size is not None:
        row["comfy_private_bytes"] = size
    return row


def append(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")


def run(path: Path, probes: Probes, every: float = EVERY_S, now: Callable[[], float] = time.time,
        sleep: Callable[[float], None] = time.sleep, ticks: int | None = None,
        stop: Callable[[], bool] = lambda: False) -> int:
    """Sample every `every` seconds until `ticks` rows or `stop()`; rows written."""
    written = 0
    while (ticks is None or written < ticks) and not (written and stop()):
        append(path, sample(probes, now()))
        written += 1
        sleep(every)
    return written


# ---- what the finish report reads --------------------------------------------------

def kind(row: dict) -> str:
    """busy (the GPU works or the queue runs), claimed (a job holds the device), idle."""
    if row.get("gpu_util", 0) >= BUSY_UTIL or row.get("queue_running", 0) > 0:
        return "busy"
    return "claimed" if row.get("claims", 0) > 0 else "idle"


def minutes_per_step(rows: list[dict], spans: list[tuple[str, float, float]], every: float = EVERY_S) -> dict:
    """{step: {busy, claimed, idle}} in minutes, each sample worth `every` seconds."""
    count = {step: {"busy": 0, "claimed": 0, "idle": 0} for step, _, _ in spans}
    for row in rows:
        for step, start, end in spans:
            if start <= row.get("ts", -1) < end:
                count[step][kind(row)] += 1
    return {step: {k: round(v * every / 60.0, 2) for k, v in got.items()} for step, got in count.items()}


def time_line(charged_s: float, wall_s: float, dead_s: float) -> str:
    """The finish report's 'charged | wall | dead' line, in hours."""
    return f"charged {charged_s / 3600:.2f} h | wall {wall_s / 3600:.2f} h | dead {dead_s / 3600:.2f} h"


def finish_line(home) -> str:
    """The drive's finish line for an episode folder: the run clock's charge, the first-start to
    last-end wall, and the dead gaps between runs (K4); the hours of the runs a kill ended
    (episode_clock.killed_part, deadline retro 2026-10-20); an owner's repair (studio/repair_clock)
    adds its own hours against its cap, never into the episode's charge."""
    from studio import episode_clock, repair_clock, run_clock
    spans = run_clock.spans(home)
    wall = max(e for _, e in spans) - min(s for s, _ in spans) if spans else 0.0
    dead = sum(g["seconds"] for g in run_clock.dead_gaps(home))
    return (time_line(run_clock.spent(home), wall, dead) + episode_clock.killed_part(home)
            + repair_clock.finish_part(home))


def step_spans(home) -> list[tuple[str, float, float]]:
    """(step id, start, end) epoch seconds of every timed step row in the folder's timing.jsonl."""
    from datetime import datetime
    path, out = Path(home) / "timing.jsonl", []
    for line in (path.read_text(encoding="utf-8").splitlines() if path.exists() else []):
        try:
            row = json.loads(line)
            if str(row.get("stage", "")).startswith("step_") and row.get("seconds"):
                end = datetime.fromisoformat(row["ended"]).timestamp()
                out.append((row["stage"][5:], end - float(row["seconds"]), end))
        except (ValueError, KeyError, TypeError):
            continue
    return out


def finish_report(home, rows: list[dict] | None = None) -> str:
    """finish_line, then busy/claimed/idle minutes per step when the GPU ledger's rows are given."""
    lines = [finish_line(home)]
    per = minutes_per_step(rows, step_spans(home)) if rows else {}
    lines += [f"  step {s}: busy {m['busy']} | claimed {m['claimed']} | idle {m['idle']} min" for s, m in per.items()]
    return "\n".join(lines)


def read_rows(path: Path = LEDGER) -> list[dict]:
    """The sampler's rows; a missing or broken file is no rows (the line still prints)."""
    try:
        return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    except (OSError, ValueError):
        return []


# ---- the real probes ----------------------------------------------------------------

def smi_probe(run_cmd=subprocess.run) -> dict:
    done = run_cmd(["nvidia-smi", "--query-gpu=memory.used,utilization.gpu", "--format=csv,noheader,nounits"],
                   capture_output=True, text=True, timeout=15, check=True)
    used, util = [int(v) for v in done.stdout.strip().splitlines()[0].split(",")]
    return {"gpu_used_mib": used, "gpu_util": util}


def host_probe() -> dict:
    from studio import engine_ops
    stat = engine_ops._memory_status()
    return {"commit_free_gb": engine_ops.commit_free_gb(lambda: stat),
            "ram_free_gb": round(stat["ullAvailPhys"] / 2**30, 2)}


def queue_probe() -> dict:
    from studio import engine_ops
    q = engine_ops.queue()
    return {"running": len(q["running_ids"]), "pending": q["pending"]}


def private_bytes(pid: int) -> int | None:
    """PrivateUsage of a process (Windows GetProcessMemoryInfo); None where unavailable."""
    import ctypes
    from ctypes import wintypes

    class Counters(ctypes.Structure):
        _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD)] + \
                   [(n, ctypes.c_size_t) for n in ("PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage",
                    "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage", "QuotaNonPagedPoolUsage",
                    "PagefileUsage", "PeakPagefileUsage", "PrivateUsage")]
    handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)         # QUERY_LIMITED_INFORMATION
    if not handle:
        return None
    counters = Counters()
    counters.cb = ctypes.sizeof(Counters)
    ok = ctypes.windll.psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb)
    ctypes.windll.kernel32.CloseHandle(handle)
    return int(counters.PrivateUsage) if ok else None


def comfy_probe() -> int | None:
    from studio import engine_ops
    from studio.command_center import procs
    rows = engine_ops.engine_rows(procs.list_processes())
    return private_bytes(rows[0].pid) if rows else None


def claims_probe() -> list:
    from studio import compute_device
    return compute_device.live_claims()


def default_probes() -> Probes:
    return Probes(queue=queue_probe, claims=claims_probe, smi=smi_probe, host=host_probe, comfy_bytes=comfy_probe)


def lock_stop(idle_exit: float, now: Callable[[], float] = time.time, lock: Path = LOCK) -> Callable[[], bool]:
    """Stop once gpu.lock has been absent for `idle_exit` seconds: the drive is over."""
    gone = [None]

    def check() -> bool:
        if lock.exists():
            gone[0] = None
            return False
        gone[0] = gone[0] if gone[0] is not None else now()
        return now() - gone[0] >= idle_exit
    return check


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--every", type=float, default=EVERY_S)
    parser.add_argument("--idle-exit", type=float, default=600.0)
    args = parser.parse_args(argv)
    run(LEDGER, default_probes(), args.every, stop=lock_stop(args.idle_exit))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
