#!/usr/bin/env python
"""Step 08 -- panels: one panel per shot, two machine gates, one contact sheet, one judge.

    uv run python scripts/episode/step_08_panels.py <codex_id> <n>

Wraps scripts/episode/panels.py, panel_check.py and panel_content_check.py
(the local vision model, GPU; re-run only when its verdict is missing or older
than a panel), writes storyboard/contact.png (studio/panel_contact), then
clears EYE_PANELS with the panel eye (studio/judges/panel_eye) on the
gates.yaml row: a pass is signed storyboard/eye_<sha8>.json in the judge's
name; a fault climbs the panel ladder (studio/panel_ladder: a redraw on a
bumped seed, then a reprose of the cell) and ends keep_best, flagged.  Nobody
is asked (decision 2026-09-24-automate-the-taste-gates).  The takes refuse
without all three verdicts.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import episode_home, eye_verdict, gate_policy, judged_gate, panel_contact, panel_dq  # noqa: E402
from studio import panel_ladder, step_cli  # noqa: E402
from studio.judges import panel_eye  # noqa: E402
from studio.judges.verdict import Verdict  # noqa: E402

STEP_ID = "08"
NAME = "panels"
GPU = True
GATE = "EYE_PANELS"
BOARD = "storyboard"
VERDICTS = ("panel_dq.json", "panel_content.json")


def panels_of(board: Path) -> list[Path]:
    return sorted(Path(board).glob("shot_*.png"))


def wanted(home: Path) -> list[int]:
    """Every shot the plan names."""
    plan = Path(home) / "plan.json"
    return [int(s["index"]) for s in (episode_home.read_json(plan).get("shots") or [])] if plan.exists() else []


def redrawn_grids(board: Path) -> list[str]:
    """Grids drawn after the last cut: the newest panel or contact sheet is the
    cut (panels.py leaves an unchanged panel's file alone, the contact is rewritten)."""
    board = Path(board)
    cut = [p.stat().st_mtime for p in panels_of(board) + [board / "contact.png"] if p.exists()]
    if not cut:
        return []
    return sorted(g.name for g in (board / "grids").glob("*.png") if g.stat().st_mtime > max(cut))


def panel_refusals(home: Path) -> list[str]:
    """Why the takes may not be built from these panels: each machine verdict
    missing, incomplete, failed or older than a panel (panel_dq.panel_refusal),
    and no eye verdict signed for these exact pictures."""
    board = Path(home) / BOARD
    panels, shots = panels_of(board), wanted(home)
    judged_ok = eye_verdict.passed(board, panels)
    out = [f"{name}: {why}" for name in VERDICTS
           if (why := panel_dq.panel_refusal(board / name, panels, shots, judged_ok=judged_ok))]
    out += [f"{g}: redrawn after the panels were cut" for g in redrawn_grids(board)]
    if not eye_verdict.passed(board, panels):
        out.append(f"no current panel eye verdict ({BOARD}/eye_<sha8>.json)")
    return out


def done(ctx) -> bool:
    board = ctx.home / BOARD
    return bool(panels_of(board)) and (board / "contact.png").exists() and not panel_refusals(ctx.home)


def checked(ctx, script: str, clock: str, verdict: str, gpu: bool = False, *extra: str) -> None:
    """Run a panel checker; one that FOUND faults hands them to the judge.

    ep12: panel_content_check exited 1 on three failing panels, run_script made
    that a refusal, and the panel judge and its redraw ladder never ran.  Exit 1
    is also a crash, so it passes only when the checker rewrote its verdict."""
    path = ctx.home / BOARD / verdict
    before = path.stat().st_mtime if path.exists() else None
    try:
        ctx.run_script(script, *extra, gpu=gpu, clock=clock)
    except SystemExit as refused:
        fresh = path.exists() and (before is None or path.stat().st_mtime > before)
        if not str(refused).endswith("exit 1") or not fresh:
            raise
        ctx.log(f"{script}: faults found; the panel judge reads them")


def rebuild(ctx, only: list[int] | None = None) -> list[Path]:
    """The panels cut, both machine gates run (the vision gate only when its
    verdict is stale), the contact sheet written; the panels as they stand.
    With `only` (a ladder rung's redrawn shots, five-hour plan fix 2c), the
    vision gate re-reads JUST those panels and merges the rows -- a full board
    read cost ~15 min a pass and ep13 paid 28 of them."""
    board = ctx.home / BOARD
    ctx.run_script("scripts/episode/panels.py", clock="panels")
    checked(ctx, "scripts/episode/panel_check.py", "panel_dq", "panel_dq.json")
    panels = panels_of(board)
    if not panels:
        raise SystemExit(f"REFUSED: no panels under {BOARD}/ after panels.py")
    if panel_dq.panel_refusal(board / "panel_content.json", panels, wanted(ctx.home)):
        checked(ctx, "scripts/episode/panel_content_check.py", "panel_content", "panel_content.json", GPU,
                *[str(i) for i in only or []])
    panel_contact.write(panels, board / "contact.png")
    return panels


def judge_of(ctx) -> Callable[[], Verdict]:
    """The panel eye over the board as it stands, the plan read afresh on
    every call (a reprose rung edits it); the readers built once; each pass
    stamped in timing.jsonl (five-hour plan fix 6)."""
    from studio import episode_clock
    readers = panel_eye.tools()

    def judge() -> Verdict:
        with episode_clock.timed(ctx.book_dir, ctx.number, "panel_eye"):
            return panel_eye.judge(ctx.home, episode_home.read_json(ctx.home / "plan.json"),
                                   book=ctx.book_dir, **readers)
    return judge


def run(ctx) -> None:
    ctx.open_step(STEP_ID)
    rebuild(ctx)
    board = ctx.home / BOARD
    policy = gate_policy.of(ctx.stage, GATE)
    climb = panel_ladder.climb(ctx, lambda only=None: rebuild(ctx, only), cap=policy.max_grids or panel_ladder.CAP)
    judged_gate.clear(ctx, GATE, judge=judge_of(ctx),
                      sign=lambda v: eye_verdict.sign_verdict(board, panels_of(board), v),
                      ladder=climb.rungs, terminal=climb.keep_best, policy=policy)


if __name__ == "__main__":
    raise SystemExit(step_cli.main(sys.modules[__name__], sys.argv))
