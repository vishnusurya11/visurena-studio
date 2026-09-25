"""The refs department's context: one unit is one (book, style) pack.

Every book made so far has one style, so the unit label is `main` (the way the
trailer's `trailer_id` is); a second style of the same book would be a second
pack folder and a second unit.  The stage has no episode number.
"""
from __future__ import annotations

from studio import episode_home
from studio.stage_run import StageContext

STAGE = "refs"
UNIT = "main"


def context(conn, codex_id: str, number: int | None = None, **kw) -> StageContext:
    ctx = StageContext(conn, codex_id, episode_home.book_dir(codex_id), STAGE, unit=UNIT, **kw)
    ctx.refs_dir = ctx.book_dir / "refs"
    return ctx
