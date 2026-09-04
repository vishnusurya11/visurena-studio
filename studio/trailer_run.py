"""What one unattended trailer run carries from step to step.

The budget (wall-clock shares under the 6 h ceiling), the tracker (events +
JSONL log), and the learnings file every ladder rung is written to.  Steps
receive the context and nothing else; they never open the database or pick
a log path themselves.
"""
from __future__ import annotations

from pathlib import Path

from studio.learnings import Learning, record
from studio.run_budget import TRAILER_CEILING_SECONDS, TRAILER_SHARES, Budget
from studio.tracking import Tracker

STAGE = "trailer"


class RunContext:
    def __init__(self, conn, codex_id: str, book_dir: Path, *, trailer_id: str = "main",
                 logs_root: Path | None = None, ceiling: float = TRAILER_CEILING_SECONDS):
        self.conn = conn
        self.codex_id = codex_id
        self.book_dir = Path(book_dir)
        self.trailer_id = trailer_id
        self.budget = Budget(ceiling, TRAILER_SHARES)
        kwargs = {"logs_root": logs_root} if logs_root else {}
        self.tracker = Tracker(conn, codex_id, STAGE, **kwargs)
        self.rungs_in_step = 0

    @property
    def out_dir(self) -> Path:
        return self.book_dir / "trailer" / self.trailer_id

    @property
    def learnings_path(self) -> Path:
        return self.out_dir / "learnings.jsonl"

    def learn(self, learning: Learning) -> None:
        """A rung was taken: write it for the retrospect and warn in the log."""
        record(self.learnings_path, learning)
        self.rungs_in_step += 1
        self.tracker.log(f"{learning.gate}: measured {learning.measured} vs "
                         f"{learning.threshold} -> {learning.action}"
                         + (" (terminal)" if learning.terminal else ""),
                         level="WARNING", step_id=learning.step)

    def open_step(self, step_id: str) -> None:
        self.budget.start(step_id)
        self.rungs_in_step = 0
