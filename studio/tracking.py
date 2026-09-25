"""Standardized run tracking for every stage: events to the DB, detail to JSONL logs.

Usage (identical across all stages and steps — see docs/db/EVENT_MODEL.md):

    tracker = Tracker(conn, codex_id, "analysis")
    with tracker.step("01_01"):
        ...work...                      # started/completed/failed events automatic
    tracker.log("chapter count = 14", step_id="01_03")

Events = what/when (tiny, permanent). Logs = why/how (verbose, disposable).
"""

from __future__ import annotations

import json
import traceback
from contextlib import contextmanager
from pathlib import Path

from studio import db

LOGS_ROOT = Path("logs")


def make_run_id(codex_id: str, stage: str) -> str:
    """Correlation id joining events to their log file: <codex>__<stage>__<utc ts>."""
    return f"{codex_id}__{stage}__{db.utc_now().strftime('%Y%m%d%H%M%S')}"


class Tracker:
    """One per stage run. Emits standardized events and JSONL log lines."""

    def __init__(self, conn, codex_id: str, stage: str, *, logs_root: Path = LOGS_ROOT,
                 unit: str | None = None):
        self.conn = conn
        self.codex_id = codex_id
        self.stage = stage
        self.unit = unit
        self.run_id = make_run_id(codex_id, stage)
        self.log_path = Path(logs_root) / codex_id / stage / f"{self.run_id}.log"

    def log(self, msg: str, *, level: str = "INFO", step_id: str = "") -> None:
        """Append one JSONL line to this run's log file."""
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        line = {
            "ts": db.utc_now().strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "level": level,
            "codex_id": self.codex_id,
            "stage": self.stage,
            "step_id": step_id,
            "msg": msg,
        }
        with open(self.log_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(line, ensure_ascii=False) + "\n")

    def event(self, step_id: str, event: str, *, detail: str | None = None) -> None:
        """One event row, stamped with this run's id."""
        db.add_event(self.conn, self.codex_id, self.stage, step_id, event,
                     run_id=self.run_id, detail=detail, unit=self.unit)

    @contextmanager
    def step(self, step_id: str):
        """started -> body -> completed; on exception: failed event (one-line detail),
        full traceback to the log, exception re-raised."""
        self.event(step_id, "started")
        self.log("started", step_id=step_id)
        try:
            yield self
        except Exception as exc:
            summary = f"{type(exc).__name__}: {exc}"[:200]
            self.event(step_id, "failed", detail=summary)
            self.log(traceback.format_exc(), level="ERROR", step_id=step_id)
            raise
        self.event(step_id, "completed")
        self.log("completed", step_id=step_id)
