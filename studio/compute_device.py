"""The device router: where a heavy NON-render job runs (owner 2026-10-18):
"if the GPU is rendering, do this on the CPU; if the GPU is empty, do it on the GPU."

`device_for(job, need_gb)` says "cuda" only when
  - the ComfyUI queue is empty (running + pending == 0), asked twice SETTLE_S apart:
    a render step between two submissions is not an idle GPU;
  - no GPU claim of ours is live (`claim()`: the av3 master pass, the whisper worker,
    any routed job that holds the card outside ComfyUI's queue);
  - and `need_gb` of VRAM is free (nvidia-smi) after ComfyUI was asked to free its
    models -- a POST /free sent ONLY once the queue read empty.
Otherwise "cpu".  Any probe that fails routes to the CPU, today's path, with its
error as the reason.  `VISURENA_DEVICE=cpu` forces the CPU (the kill switch).

Every decision is printed and appended to library/.device/decisions.jsonl with its
reason ("GPU idle", "render running (1 running, 0 pending)").  Every probe is
injectable (`probe=`); no test reaches ComfyUI or nvidia-smi.

This module is pure stdlib so ComfyUI's embedded python can import it too.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import uuid
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable, Mapping

ROOT = Path(__file__).resolve().parents[1]
CLAIMS = ROOT / "library" / ".device" / "claims"
LOG = ROOT / "library" / ".device" / "decisions.jsonl"
SETTING = "VISURENA_DEVICE"
SETTLE_S = 2.0
"""The second look at the queue: one render step's next submission lands within it."""
STALE_S = 6 * 3600.0
"""A claim older than an episode's whole budget is a crashed holder's, not a live job."""
VRAM_POLLS, VRAM_GAP_S = 3, 1.0
"""/free returns before the memory does; nvidia-smi is read up to three times."""


@dataclass(frozen=True)
class Decision:
    job: str
    device: str
    reason: str
    at: float = field(default_factory=time.time)

    def line(self) -> str:
        return f"DEVICE {self.job} -> {self.device}: {self.reason}"


@dataclass(frozen=True)
class Probe:
    queue: Callable[[], tuple[int, int]]
    free_mb: Callable[[], int | None]
    free_models: Callable[[], None]
    claims: Callable[[], list[dict]]
    sleep: Callable[[float], object]
    env: Mapping[str, str]


# ---- the parts ---------------------------------------------------------------------

def parse_free_mb(text: str) -> int | None:
    """The first GPU's free MiB off `nvidia-smi --query-gpu=memory.free`, or None."""
    first = (text or "").strip().splitlines()[:1]
    try:
        return int(first[0].strip()) if first else None
    except ValueError:
        return None


def smi_free_mb(run=subprocess.run) -> int | None:
    """Free VRAM now; None when nvidia-smi cannot answer (a lost GPU, no driver)."""
    try:
        done = run(["nvidia-smi", "--query-gpu=memory.free", "--format=csv,noheader,nounits"],
                   capture_output=True, text=True, timeout=15)
    except (OSError, subprocess.SubprocessError):
        return None
    return parse_free_mb(done.stdout) if done.returncode == 0 else None


def live_claims(root: Path | None = None, now: float | None = None) -> list[dict]:
    """Every readable claim younger than STALE_S."""
    now, out = time.time() if now is None else now, []
    for path in sorted(Path(root or CLAIMS).glob("*.json")):
        try:
            row = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(row, dict) and now - float(row.get("at", 0)) < STALE_S:
            out.append(row)
    return out


@contextmanager
def claim(job: str, root: Path | None = None):
    """Hold the GPU for `job` outside ComfyUI's queue; released however the job ends."""
    folder = Path(root or CLAIMS)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{os.getpid()}_{uuid.uuid4().hex[:8]}.json"
    path.write_text(json.dumps({"job": job, "pid": os.getpid(), "at": time.time()}), encoding="utf-8")
    try:
        yield path
    finally:
        path.unlink(missing_ok=True)


def write_decision(decision: Decision, path: Path | None = None) -> None:
    target = Path(path or LOG)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as out:
        out.write(json.dumps(asdict(decision)) + "\n")


def say(decision: Decision) -> None:
    """The default log: the run's own log line, and the decisions file."""
    print(decision.line(), file=sys.stderr, flush=True)
    try:
        write_decision(decision)
    except OSError:
        pass


# ---- the decision ------------------------------------------------------------------

def blocker(probe: Probe) -> str | None:
    """Why the GPU is not idle now, or None."""
    if str(probe.env.get(SETTING, "")).lower() == "cpu":
        return f"{SETTING}=cpu"
    running, pending = probe.queue()
    if running:
        return f"render running ({running} running, {pending} pending)"
    if pending:
        return f"render queued ({pending} pending)"
    held = probe.claims()
    return f"GPU held by {', '.join(str(c.get('job')) for c in held)}" if held else None


def vram_short(probe: Probe, need_gb: float) -> str | None:
    """Why the VRAM will not hold the job after a /free, or None.  Called only once
    the queue read empty twice."""
    probe.free_models()
    free = None
    for k in range(VRAM_POLLS):
        free = probe.free_mb()
        if free is None or free >= need_gb * 1024:
            break
        probe.sleep(VRAM_GAP_S)
    if free is None:
        return "nvidia-smi unreadable"
    return None if free >= need_gb * 1024 else f"VRAM {free / 1024:.1f} GB free < {need_gb:g} GB needed"


def why_not(probe: Probe, need_gb: float) -> str | None:
    """The first reason the job may not take the GPU, looking twice at the queue."""
    why = blocker(probe)
    if why is None:
        probe.sleep(SETTLE_S)
        why = blocker(probe)
    return why if why is not None else vram_short(probe, need_gb)


def default_probe() -> Probe:
    from studio import comfy
    return Probe(queue=comfy.queue_counts, free_mb=smi_free_mb, free_models=comfy.free_models,
                 claims=live_claims, sleep=time.sleep, env=os.environ)


def device_for(job: str, need_gb: float, probe: Probe | None = None,
               log: Callable[[Decision], object] | None = None) -> str:
    """"cuda" when the GPU is idle and roomy enough, else "cpu"; logged with its reason."""
    try:
        why = why_not(probe or default_probe(), need_gb)
    except Exception as failed:              # a probe's failure is the CPU's, never a crash
        why = f"router error {type(failed).__name__}: {failed}"
    decision = Decision(job, "cpu" if why else "cuda", why or "GPU idle")
    (log or say)(decision)
    return decision.device
