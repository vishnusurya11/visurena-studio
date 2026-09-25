#!/usr/bin/env python
"""Step 08 -- panels: one panel per shot, two machine gates, one contact sheet, one eye.

    uv run python scripts/episode/step_08_panels.py <codex_id> <n>

Wraps scripts/episode/panels.py, panel_check.py and panel_content_check.py
(the local vision model, GPU; re-run only when its verdict is missing or older
than a panel), writes storyboard/contact.png (studio/panel_contact), then
asks for the eye: storyboard/eye_<sha8>.json, signed with
scripts/episode/sign_eye.py.  The takes refuse without all three verdicts.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import episode_home, eye_verdict, panel_contact, panel_dq, step_cli  # noqa: E402

STEP_ID = "08"
NAME = "panels"
GPU = True
BOARD = "storyboard"
VERDICTS = ("panel_dq.json", "panel_content.json")
ASK = ("look at storyboard/contact.png; sign with "
       "scripts/episode/sign_eye.py <codex_id> <n> panels pass|fault \"<what was seen>\"")


def panels_of(board: Path) -> list[Path]:
    return sorted(Path(board).glob("shot_*.png"))


def wanted(home: Path) -> list[int]:
    """Every shot the plan names."""
    plan = Path(home) / "plan.json"
    return [int(s["index"]) for s in (episode_home.read_json(plan).get("shots") or [])] if plan.exists() else []


def panel_refusals(home: Path) -> list[str]:
    """Why the takes may not be built from these panels: each machine verdict
    missing, incomplete, failed or older than a panel (panel_dq.panel_refusal),
    and the eye not signed for these exact pictures."""
    board = Path(home) / BOARD
    panels, shots = panels_of(board), wanted(home)
    out = [f"{name}: {why}" for name in VERDICTS
           if (why := panel_dq.panel_refusal(board / name, panels, shots))]
    if not eye_verdict.passed(board, panels):
        out.append(f"no current panel eye verdict ({BOARD}/eye_<sha8>.json)")
    return out


def done(ctx) -> bool:
    board = ctx.home / BOARD
    return bool(panels_of(board)) and (board / "contact.png").exists() and not panel_refusals(ctx.home)


def run(ctx) -> None:
    board = ctx.home / BOARD
    ctx.run_script("scripts/episode/panels.py", clock="panels")
    ctx.run_script("scripts/episode/panel_check.py", clock="panel_dq")
    panels = panels_of(board)
    if not panels:
        raise SystemExit(f"REFUSED: no panels under {BOARD}/ after panels.py")
    if panel_dq.panel_refusal(board / "panel_content.json", panels, wanted(ctx.home)):
        ctx.run_script("scripts/episode/panel_content_check.py", gpu=GPU, clock="panel_content")
    panel_contact.write(panels, board / "contact.png")
    eye_verdict.require(board, panels, "EYE", ASK, home=ctx.home)


if __name__ == "__main__":
    raise SystemExit(step_cli.main(sys.modules[__name__], sys.argv))
