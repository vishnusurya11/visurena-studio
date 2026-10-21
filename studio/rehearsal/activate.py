"""Arm a rehearsal process (2026-10-21_ep02_proof 1.1, 2.6): refuse while the real autopilot
could run, point temp files into the sandbox, install the fence, then the fakes and trace.

`install()` is called by studio/__init__.py in EVERY Python process; without a manifest it
returns False at once.  The scheduler query is the one read-only `schtasks` call a rehearsal
makes, and it is made BEFORE the fence's hook exists (the fence refuses schtasks after)."""
from __future__ import annotations

import csv
import importlib
import importlib.util
import io
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Callable, Mapping

from studio import settings
from studio.rehearsal import fence

TASK = "visurena-autopilot"
_INSTALLED = False


class RehearsalRefused(RuntimeError):
    """A rehearsal may not start: the real autopilot could run, or the fakes are missing."""


def schtasks_query() -> str:
    """The scheduler's CSV for the real task; '' when it cannot say (no task, not Windows)."""
    try:
        out = subprocess.run(["schtasks", "/query", "/tn", TASK, "/fo", "csv"],
                             capture_output=True, text=True, timeout=30, check=False)
    except (OSError, subprocess.SubprocessError):
        return ""
    return out.stdout if out.returncode == 0 else ""


def task_enabled(text: str) -> bool:
    """Any row of the task whose Status is not Disabled (Ready and Running are enabled)."""
    rows = list(csv.DictReader(io.StringIO(text.strip())))
    return any((row.get("Status") or "").strip() != "Disabled" for row in rows)


def unpaused_series(library: Path) -> list[Path]:
    """Every book's autopilot/series.json (one level deep, never walked) that is not held:
    held means `paused: true` or a STOP file beside it, as scripts/episode/autopilot.is_paused."""
    found = sorted(Path(library).glob("*/autopilot/series.json")) + sorted(Path(library).glob(".autopilot/series.json"))
    return [p for p in found if not (_paused(p) or (p.parent / "STOP").exists())]


def _paused(path: Path) -> bool:
    try:
        return bool(json.loads(path.read_text(encoding="utf-8")).get("paused"))
    except (OSError, ValueError):
        return False


def refuse_live_autopilot(schtasks: Callable[[], str], series: Callable[[], list]) -> None:
    if task_enabled(schtasks()):
        raise RehearsalRefused(f"the real Task Scheduler entry {TASK} is enabled; disable it before a rehearsal "
                               f"(schtasks /change /tn {TASK} /disable)")
    if held := series():
        raise RehearsalRefused(f"a real series is unpaused: {', '.join(map(str, held))}")


def point_tempdir(box: Path) -> None:
    """Every temp file of the process lands in <sandbox>/tmp (R19: shared with real runs otherwise)."""
    tmp = box / "tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    tempfile.tempdir = str(tmp)
    os.environ["TMP"] = os.environ["TEMP"] = str(tmp)


def module_present(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def load_fakes(manifest: Mapping) -> None:
    """fakes.install(manifest); a rehearsal without its fakes would reach real engines, so it
    refuses, unless the manifest says `fakes: false` (the fence's own tests)."""
    if manifest.get("fakes") is False:
        return
    if not module_present("studio.rehearsal.fakes"):
        raise RehearsalRefused("studio.rehearsal.fakes is absent and the manifest does not say fakes: false")
    importlib.import_module("studio.rehearsal.fakes").install(manifest)


def load_trace(manifest: Mapping) -> None:
    if module_present("studio.rehearsal.trace"):
        importlib.import_module("studio.rehearsal.trace").install(manifest)


def install(manifest: Mapping | None = None, *, env: Mapping[str, str] = os.environ,
            schtasks: Callable[[], str] = schtasks_query, series: Callable[[], list] | None = None) -> bool:
    """Arm this process for the rehearsal its manifest names; False (and nothing done) without one."""
    global _INSTALLED
    manifest = settings.rehearsal(env) if manifest is None else manifest
    if manifest is None or _INSTALLED:
        return False
    libraries = settings.real_libraries(env)
    refuse_live_autopilot(schtasks, series or (lambda: [p for lib in libraries for p in unpaused_series(lib)]))
    point_tempdir(settings.sandbox(env))
    fence.install(fence.Fence.from_settings(env))
    load_fakes(manifest)
    load_trace(manifest)
    _INSTALLED = True
    return True
