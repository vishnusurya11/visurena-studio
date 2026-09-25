"""The episode line's context: one unit is one episode folder, `epNN`.

Unit grammar for this stage today: `ep` + two digits, the folder under
`library/<book>/episodes/`.  One chapter is one episode in every book made so
far; a unit that spans chapters is a new folder name, never a renamed one
(decision 2026-09-24, D2).

The context carries what the trailer's does and the stage context lacks: the
wall-clock budget under the episode ceiling (the render approval, as GPU
hours) and the learnings file every ladder rung is written to.
"""
from __future__ import annotations

from pathlib import Path

from studio import episode_home
from studio.learnings import Learning, record
from studio.run_budget import EPISODE_CEILING_SECONDS, EPISODE_SHARES, Budget
from studio.stage_run import StageContext, require_registered

STAGE = "episode"


def unit_of(number: int) -> str:
    return f"ep{number:02d}"


class EpisodeContext(StageContext):
    def __init__(self, *args, ceiling: float = EPISODE_CEILING_SECONDS, **kw):
        super().__init__(*args, **kw)
        self.budget = Budget(ceiling, EPISODE_SHARES)
        self.rungs_in_step = 0
        self.home: Path | None = None

    @property
    def learnings_path(self) -> Path:
        return Path(self.home) / "learnings.jsonl"

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


def context(conn, codex_id: str, number: int | None, **kw) -> EpisodeContext:
    if number is None:
        raise SystemExit("the episode stage needs an episode number: <codex_id> <n>")
    require_registered(conn, codex_id)
    ctx = EpisodeContext(conn, codex_id, episode_home.book_dir(codex_id), STAGE,
                         unit=unit_of(number), number=number, **kw)
    ctx.home = episode_home.home(ctx.book_dir, number)
    return ctx
