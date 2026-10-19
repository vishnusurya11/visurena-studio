"""The episode line's context: one unit is one episode folder, `epNN`.

Unit grammar for this stage today: `ep` + two digits, the folder under
`library/<book>/episodes/`.  One chapter is one episode in every book made so
far; a unit that spans chapters is a new folder name, never a renamed one
(decision 2026-09-24, D2).

The context carries what the trailer's does and the stage context lacks: the
wall-clock budget under the episode ceiling (the render approval, as GPU
hours) and the learnings file every ladder rung is written to.

An owner's redo of a DELIVERED episode swaps that budget, once the runner has
taken the orders, for the repair window's own (studio/repair_clock, owner
ruling 2026-10-19): charged from the repair's start, capped, logged apart.
"""
from __future__ import annotations

from pathlib import Path

from studio import episode_home, repair_clock, run_budget, run_clock
from studio.learnings import Learning, record
from studio.run_budget import EPISODE_CEILING_SECONDS, EPISODE_SHARES, OWNER_LIMIT_SECONDS, Budget
from studio.stage_run import StageContext, require_registered

STAGE = "episode"


def unit_of(number: int) -> str:
    return f"ep{number:02d}"


class EpisodeContext(StageContext):
    def __init__(self, *args, ceiling: float = EPISODE_CEILING_SECONDS, **kw):
        super().__init__(*args, **kw)
        self.budget = Budget(ceiling, EPISODE_SHARES, limit=OWNER_LIMIT_SECONDS)
        self.rungs_in_step = 0
        self.home: Path | None = None
        self.repair_window: dict | None = None   # an owner's repair of a delivered episode (repair_clock)
        self.cap_said = False

    @property
    def learnings_path(self) -> Path:
        return Path(self.home) / "learnings.jsonl"

    def learn(self, learning: Learning) -> None:
        """A rung was taken: write it for the retrospect and warn in the log.
        A PASS is written too (the publish lock reads the last row per gate),
        but it is not a rung and not a warning."""
        record(self.learnings_path, learning)
        passed = learning.action == "pass"
        self.rungs_in_step += 0 if passed else 1
        self.tracker.log(f"{learning.gate}: measured {learning.measured} vs "
                         f"{learning.threshold} -> {learning.action}"
                         + (" (terminal)" if learning.terminal else ""),
                         level="INFO" if passed else "WARNING", step_id=learning.step)

    def open_step(self, step_id: str) -> None:
        self.budget.start(step_id)
        self.rungs_in_step = 0

    def after_orders(self) -> None:
        """The runner took the owner's orders: an owner redo of a DELIVERED episode opens (or a
        relaunch continues) its repair window, and the drive runs on the repair's own capped clock
        (owner ruling 2026-10-19).  Any other run keeps the episode's 6 h budget, untouched."""
        live = run_clock.read_open(self.home) or {}
        started = live.get("started") if live.get("run_id") == self.tracker.run_id else None
        window = repair_clock.window_for(self.conn, self.home, started)
        if window is not None:
            self.repair(window)

    def repair(self, window: dict) -> None:
        """The budget charged from the window's start under its cap; this run's clock row tagged."""
        episode_s = run_budget.spent_before(self.home)
        run_clock.tag_repair(self.home, self.tracker.run_id)
        self.budget, self.repair_window = repair_clock.budget(self.home, window), window
        self.say(repair_clock.open_line(self.home, window, episode_s))

    def before_step(self, step_id: str) -> None:
        """Before a step runs: a spent repair clock says CAP once (its rungs and checks are cut)."""
        window = self.repair_window
        if window is None or self.cap_said or not repair_clock.capped(self.home, window):
            return
        self.cap_said = True
        self.say(repair_clock.cap_line(self.home, window), step_id)

    def say(self, line: str, step_id: str = "") -> None:
        print(line, flush=True)
        self.log(line, step_id=step_id, level="WARNING")


def context(conn, codex_id: str, number: int | None, **kw) -> EpisodeContext:
    if number is None:
        raise SystemExit("the episode stage needs an episode number: <codex_id> <n>")
    require_registered(conn, codex_id)
    ctx = EpisodeContext(conn, codex_id, episode_home.book_dir(codex_id), STAGE,
                         unit=unit_of(number), number=number, **kw)
    ctx.home = episode_home.home(ctx.book_dir, number)
    ctx.budget.charge(run_budget.spent_before(ctx.home))   # the ceiling covers the EPISODE (fix 1)
    return ctx
