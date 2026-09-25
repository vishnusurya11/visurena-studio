"""What one unit of a format line carries from step to step.

The connection, the book, the unit, the tracker (events + JSONL log), the
GPU queue guard and the brake.  Steps receive the context and nothing else;
a step that wraps an existing script launches it through `run_script`, under
the same clock and the same one-GPU rule `scripts/episode/run.py` enforced by
hand.
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

from studio import approval, comfy, episode_clock
from studio.tracking import Tracker

WAIT_POLL = 20.0
WAIT_CAP = 7200.0
"""How often the queue is asked, and how long before waiting is itself refused
(two hours covers a full run of thirty takes)."""


def launch(cmd: list[str]) -> int:
    """Run one script to completion in its own process; its exit code comes back."""
    return subprocess.run(cmd).returncode


class StageContext:
    def __init__(self, conn, codex_id: str, book_dir: Path, stage: str, *, unit: str | None = None,
                 number: int | None = None, logs_root: Path | None = None, busy=None,
                 hold: Path = approval.HOLD, launch=launch):
        self.conn = conn
        self.codex_id = codex_id
        self.book_dir = Path(book_dir)
        self.stage = stage
        self.unit = unit
        self.number = number
        kwargs = {"logs_root": logs_root} if logs_root else {}
        self.tracker = Tracker(conn, codex_id, stage, unit=unit, **kwargs)
        self.busy = busy or comfy.busy
        self.hold = Path(hold)
        self.launch = launch
        self.sleep = time.sleep
        self.wait_cap = WAIT_CAP
        self.wait_poll = WAIT_POLL

    @property
    def label(self) -> str:
        return f"{self.codex_id} {self.stage}/{self.unit or 'book'}"

    def held(self) -> bool:
        return self.hold.exists()

    def log(self, msg: str, *, step_id: str = "", level: str = "INFO") -> None:
        self.tracker.log(msg, level=level, step_id=step_id)

    def command(self, script: str, extra: tuple[str, ...] = ()) -> list[str]:
        args = [sys.executable, script, self.codex_id]
        if self.number is not None:
            args.append(str(self.number))
        return [*args, *extra]

    def wait_free(self) -> bool:
        waited = 0.0
        while self.busy():
            if waited >= self.wait_cap:
                return False
            self.sleep(self.wait_poll)
            waited += self.wait_poll
        return True

    def run_script(self, script: str, *extra: str, gpu: bool = False, clock: str | None = None) -> int:
        """Launch an existing script as this step's body.  A GPU script waits for the
        queue to drain (one GPU, one stage) and is refused when it never does; a
        non-zero exit is a refusal that names the code.  Stamped on the unit's clock
        when it has one."""
        if gpu and not self.wait_free():
            raise SystemExit(f"REFUSED: ComfyUI's queue stayed busy for {self.wait_cap:.0f} s; "
                             f"{script} was not started")
        cmd = self.command(script, extra)
        if self.number is not None and clock:
            with episode_clock.timed(self.book_dir, self.number, clock, note=" ".join(extra)):
                rc = self.launch(cmd)
        else:
            rc = self.launch(cmd)
        if rc:
            raise SystemExit(f"REFUSED: {script} exit {rc}")
        return rc
