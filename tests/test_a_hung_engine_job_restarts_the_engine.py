"""ep27 (2026-10-09 18:18Z): a grid job sat in ComfyUI for an hour and grids.py
raised `studio.comfy.StillRunning: <id> still running after 3600s`; ComfyUI no
longer answered /queue.  The table had no row for it, so the generic 'REFUSED:
grids.py exit 1' went to the brain.  A job the engine never finished is the
engine's fault: restart it, then the step runs again."""
from __future__ import annotations

from studio import autopilot

TAIL = ("ep27_grid_kitchen_2x2: shots [8, 9, 10, 11] | slots ['101'] | prompt 4120 chars\n"
        "studio.comfy.StillRunning: c8aad4ef-e93d-49bc-aee5-b27fd859360c still running after 3600s\n"
        "Traceback (most recent call last):\n"
        "SystemExit: REFUSED: scripts/episode/grids.py exit 1\n"
        "RuntimeError: REFUSED: scripts/episode/grids.py exit 1\n")


def test_a_job_still_running_after_its_wait_restarts_comfy():
    kind, reason, order = autopilot.classify(TAIL, set())
    assert (kind, reason) == ("cure", "engine_hung")
    assert order == ("comfy_restart", None)
