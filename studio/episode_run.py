"""The episode line's context: one unit is one episode folder, `epNN`.

Unit grammar for this stage today: `ep` + two digits, the folder under
`library/<book>/episodes/`.  One chapter is one episode in every book made so
far; a unit that spans chapters is a new folder name, never a renamed one
(decision 2026-09-24, D2).
"""
from __future__ import annotations

from studio import episode_home
from studio.stage_run import StageContext, require_registered

STAGE = "episode"


def unit_of(number: int) -> str:
    return f"ep{number:02d}"


def context(conn, codex_id: str, number: int | None, **kw) -> StageContext:
    if number is None:
        raise SystemExit("the episode stage needs an episode number: <codex_id> <n>")
    require_registered(conn, codex_id)
    ctx = StageContext(conn, codex_id, episode_home.book_dir(codex_id), STAGE,
                       unit=unit_of(number), number=number, **kw)
    ctx.home = episode_home.home(ctx.book_dir, number)
    return ctx
