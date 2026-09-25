"""Episode stage runner -- one unit is one episode folder.  A SIBLING of trailer.py.

    uv run python episode.py <codex_id> <n> [--flag ...]   # one unit
    uv run python episode.py <codex_id>                    # every episodes/epNN with a plan, ascending

Steps come from the `episode` stage of stages.yaml (studio/step_runner); a
step whose output is on disk is skipped; an owner gate parks the unit with an
`escalated` event and the call-sheet line, and the runner exits 2 having marked
nothing failed.  Flags after the unit reach the step that runs (`ctx.extra`).
Zero credits: every model is the local ComfyUI.  ffmpeg is asked for BEFORE
the run opens, as trailer.py learned to.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

from studio import db, episode_home, episode_run, step_runner

STAGE = episode_run.STAGE
TOOLS = ("ffmpeg",)
PARKED = 2


def preflight(tools: tuple[str, ...] = TOOLS) -> list[str]:
    """Every tool's resolved path, or a refusal naming the first one missing."""
    found = []
    for name in tools:
        path = shutil.which(name)
        if path is None:
            raise SystemExit(f"REFUSED: {name} is not on PATH; nothing was started")
        found.append(path)
    return found


def units(book: Path) -> list[int]:
    """Every episode folder that has a plan, ascending."""
    root = Path(book) / "episodes"
    if not root.is_dir():
        return []
    return sorted(int(p.name[2:]) for p in root.glob("ep[0-9][0-9]") if (p / "plan.json").exists())


def parse(argv: list[str]) -> tuple[str, int | None, list[str]]:
    """(codex_id, episode number or None, the --flags)."""
    plain = [a for a in argv if not a.startswith("--")]
    if not plain:
        raise SystemExit("usage: episode.py <codex_id> [<n>] [--flag ...]")
    number = int(plain[1]) if len(plain) > 1 and plain[1].isdigit() else None
    return plain[0], number, [a for a in argv if a.startswith("--")]


def process(conn, codex_id: str, number: int, extra: list[str], **kw) -> str:
    """One unit through every step: 'completed' or 'escalated'; a failure raises
    after the stage is marked failed."""
    ctx = episode_run.context(conn, codex_id, number, **kw)
    ctx.extra = list(extra)
    print(f"=== EPISODE start | {ctx.label} | run {ctx.tracker.run_id} ===")
    db.mark_stage(conn, ctx.codex_id, STAGE, "running")
    try:
        outcome = step_runner.run_steps(ctx, step_runner.load_steps(STAGE))
    except Exception:
        db.mark_stage(conn, ctx.codex_id, STAGE, "failed")
        raise
    if outcome == "completed":
        db.mark_stage(conn, ctx.codex_id, STAGE, "completed")
    print(f"=== EPISODE {outcome} | {ctx.label} ===")
    return outcome


def main(argv: list[str], conn=None, tools: tuple[str, ...] = TOOLS, **kw) -> int:
    codex_id, number, extra = parse(argv)
    conn = conn or db.get_connection()
    db.init_db(conn)
    preflight(tools)
    numbers = [number] if number is not None else units(episode_home.book_dir(codex_id))
    if not numbers:
        raise SystemExit(f"REFUSED: no episodes/epNN folder with a plan.json for {codex_id}")
    outcomes = [process(conn, codex_id, n, extra, **kw) for n in numbers]
    return PARKED if "escalated" in outcomes else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
