"""S0a's checkpoints, cut only BETWEEN steps (2026-10-21_ep02_proof DESIGN 3, the checkpoint maker).

A checkpoint is the sandbox copied while no drive runs, at the moment a drive stopped in front of
step NN: `after_<NN-1>`.  The real boundary flag cannot make that moment: the runner reads it
between steps, but takes_r2v, the take ladder and every judged rung read it too, so a flag set
while step 09 runs stops 09 between two takes and cuts it into one take per launch.

So no flag file is ever written.  In a rehearsal child, studio.step_runner's `boundary` is this
module's `Between`: the real module in every respect, except that the runner's OWN between-steps
check (the call from `run_steps`, line `if boundary.requested(...)` before a step starts) also
answers True in front of a step whose wanted checkpoint is not made yet.  The real runner then
stops the unit `PAUSED AT BOUNDARY | ... | before step NN` and the drive exits as from a pause; a
mid-step check (a take, a rung) calls `studio.boundary` itself and never sees this stop.  The stop
leaves `<sandbox>/checkpoint.pending`; the supervisor copies it while the drive is down, before
any relaunch (its pre-tick hook, else the relaunch's own drive argv)."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Callable, Iterable, Mapping

WANTED = ("after_02", "after_05", "after_07", "after_08", "after_09", "after_12")
"""The checkpoints the fault scenarios restore from (rehearse.TABLE)."""
PENDING = "checkpoint.pending"


def wanted(manifest: Mapping) -> tuple[str, ...]:
    """The manifest's checkpoint list: `checkpoints: true` is every WANTED one."""
    asked = manifest.get("checkpoints")
    return WANTED if asked is True else tuple(asked or ())


def due(box: Path, names: Iterable[str], step_id: str) -> str | None:
    """`after_<NN-1>` when it is wanted, not made and not already pending; else None."""
    try:
        name = f"after_{int(step_id) - 1:02d}"
    except (TypeError, ValueError):
        return None
    made = (Path(box) / "checkpoints" / name).is_dir() or pending(box) is not None
    return name if name in set(names) and not made else None


def mark(box: Path, name: str) -> None:
    (Path(box) / PENDING).write_text(json.dumps({"name": name}), encoding="utf-8")


def pending(box: Path) -> str | None:
    try:
        return str(json.loads((Path(box) / PENDING).read_text(encoding="utf-8"))["name"])
    except (OSError, ValueError, KeyError, TypeError):
        return None


class Between:
    """step_runner's `boundary` in a rehearsal: the real module, plus the stop in front of a due step."""

    def __init__(self, real, box: Path, names: Iterable[str]):
        self.real, self.box, self.names = real, Path(box), tuple(names)

    def __getattr__(self, name: str):
        return getattr(self.real, name)

    def requested(self, home) -> bool:
        if self.real.requested(home):
            return True
        caller = sys._getframe(1)
        if caller.f_code.co_name != "run_steps":           # _run_one's check after a failure: the real flag only
            return False
        name = due(self.box, self.names, getattr(caller.f_locals.get("step"), "STEP_ID", None))
        if name:
            mark(self.box, name)
        return name is not None


def shim(step_runner, box: Path, names: Iterable[str]) -> Callable[[], None]:
    """Put `Between` in place of step_runner's `boundary`; the undo puts the real one back."""
    real = step_runner.boundary
    step_runner.boundary = Between(real, box, names)
    return lambda: setattr(step_runner, "boundary", real)


def take(box: Path, launching: bool = False) -> str | None:
    """Copy the pending checkpoint (the drive is down) and clear it; its name, or None.  From a
    relaunch (`launching`), the launch log the autopilot just opened is left out of the copy."""
    from studio import settings
    from studio.rehearsal import sandbox
    name = pending(box)
    if name is None:
        return None
    dest = sandbox.checkpoint(Path(box), name)
    opened = (dest / settings.LIBRARY_DIR).glob("*/episodes/ep*/drive_launch*.log") if launching else ()
    for log in opened:
        if log.stat().st_size == 0:
            log.unlink()
    (Path(box) / PENDING).unlink(missing_ok=True)
    return name


def install(manifest: Mapping, box: Path) -> None:
    """In a rehearsal child whose manifest asks for checkpoints: the shim lands as step_runner loads."""
    names = wanted(manifest)
    if names:
        from studio.rehearsal import fence
        fence.patch_on_import("studio.step_runner", lambda mod: shim(mod, box, names))
