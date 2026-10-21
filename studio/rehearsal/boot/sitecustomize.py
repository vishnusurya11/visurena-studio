"""The rehearsal boot (2026-10-21_ep02_proof P1): a rehearsal puts this folder first on
PYTHONPATH (activate.arm_children), so EVERY Python child arms its fence before its own code
runs, even a bare `python -c` or worker script that never imports studio.

Outside a rehearsal (no VISURENA_LIBRARY) it does nothing.  site.py reports an Exception from
sitecustomize and runs the child anyway, so a failure here ends the process instead: a child
that cannot arm must not run.  Children started with -I/-E/-S skip this file; the fence refuses
those launches."""
import os
import sys

if os.environ.get("VISURENA_LIBRARY"):
    try:
        import studio  # noqa: F401  studio/__init__ runs activate.install(), which arms the fence
    except BaseException as exc:  # noqa: BLE001  fail closed: never a silent unfenced child
        sys.stderr.write(f"rehearsal boot refused this child: {exc!r}\n")
        sys.stderr.flush()
        os._exit(86)
