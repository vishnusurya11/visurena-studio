"""Arm a rehearsal process (2026-10-21_ep02_proof 1.1, 2.6): refuse while the real autopilot
could run, point temp files into the sandbox, arm every Python child, install the fence, then
the fakes and trace.

`install()` is called by studio/__init__.py in EVERY Python process (and by the rehearsal boot's
sitecustomize in every Python child); without a manifest it returns False at once.  The
scheduler query is the one read-only `schtasks` call per rehearsal: the first process makes it
BEFORE its fence exists (the fence refuses schtasks after), and its children inherit the
verdict through VISURENA_REHEARSAL_CLEARED for CLEARANCE_S.  A query that cannot say refuses."""
from __future__ import annotations

import csv
import importlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Callable, Mapping

from studio import settings
from studio.rehearsal import fence

TASK = "visurena-autopilot"
NOT_FOUND = "cannot find the file specified"
"""schtasks' English stderr for a task that does not exist (any other answer cannot say)."""
CLEARED = "VISURENA_REHEARSAL_CLEARED"
CLEARANCE_S = 1800
"""How long a parent's scheduler verdict stands for its children: `<epoch>|<sandbox>`."""
_INSTALLED = False


class RehearsalRefused(RuntimeError):
    """A rehearsal may not start: the real autopilot could run, or the fakes are missing."""


def schtasks_query() -> str | None:
    """The scheduler's CSV for the real task; '' when there surely is none (schtasks says the task
    does not exist, or there is no Task Scheduler: not Windows); None when it cannot say (a failed,
    timed-out or other-language answer), which refuses the rehearsal: fail closed."""
    if sys.platform != "win32":
        return ""
    try:
        out = subprocess.run(["schtasks", "/query", "/tn", TASK, "/fo", "csv"],
                             capture_output=True, text=True, timeout=30, check=False)
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode == 0:
        return out.stdout
    return "" if NOT_FOUND in (out.stderr or "").lower() else None


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


def refuse_live_autopilot(schtasks: Callable[[], str | None], series: Callable[[], list]) -> None:
    answer = schtasks()
    if answer is None:
        raise RehearsalRefused(f"cannot read the Task Scheduler entry {TASK} (the query failed or timed out); "
                               f"a rehearsal starts only when the scheduler says it is disabled or absent")
    if task_enabled(answer):
        raise RehearsalRefused(f"the real Task Scheduler entry {TASK} is enabled; disable it before a rehearsal "
                               f"(schtasks /change /tn {TASK} /disable)")
    if held := series():
        raise RehearsalRefused(f"a real series is unpaused: {', '.join(map(str, held))}")


def cleared(env: Mapping[str, str], box: Path) -> bool:
    """A parent rehearsal process checked the scheduler and the series for THIS sandbox under
    CLEARANCE_S ago: its children inherit the verdict instead of each querying schtasks again."""
    stamp, _, where = (env.get(CLEARED) or "").partition("|")
    try:
        age = time.time() - int(stamp)
    except ValueError:
        return False
    same = bool(where) and os.path.normcase(os.path.abspath(where)) == os.path.normcase(os.path.abspath(box))
    return same and 0 <= age < CLEARANCE_S


def mark_cleared(box: Path) -> None:
    os.environ[CLEARED] = f"{int(time.time())}|{box}"


def clear_or_refuse(env: Mapping[str, str], box: Path, schtasks: Callable, series: Callable) -> None:
    """The one read-only scheduler query per rehearsal (children inherit it), or a refusal."""
    if cleared(env, box):
        return
    refuse_live_autopilot(schtasks, series)
    mark_cleared(box)


def arm_children() -> None:
    """Put the rehearsal boot first on PYTHONPATH: every Python child this process launches arms
    its own fence at start, even one that never imports studio (a bare `python -c`)."""
    boot = str(fence.BOOT)
    rest = [p for p in os.environ.get("PYTHONPATH", "").split(os.pathsep)
            if p and os.path.normcase(p) != os.path.normcase(boot)]
    os.environ["PYTHONPATH"] = os.pathsep.join([boot, *rest])


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
    libraries, box = settings.real_libraries(env), settings.sandbox(env)
    clear_or_refuse(env, box, schtasks, series or (lambda: [p for lib in libraries for p in unpaused_series(lib)]))
    point_tempdir(box)
    arm_children()
    fence.install(fence.Fence.from_settings(env))
    load_fakes(manifest)
    load_trace(manifest)
    _INSTALLED = True
    return True
