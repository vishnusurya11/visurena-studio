"""A grid redrawn after its panels were cut makes the panels stale.

ep13, 2026-09-27: step 07 redrew 13 grids and step 08 said 'skipped: output
exists' -- the old panels, cut from the old grids, still carried their verdicts,
and the takes would have been built from pictures no longer on the board.
"""
import importlib.util
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("step_08_stale", ROOT / "scripts/episode/step_08_panels.py")
step = importlib.util.module_from_spec(_spec)
sys.modules["step_08_stale"] = step
_spec.loader.exec_module(step)


def board(tmp_path, grid_at: float, panel_at: float) -> Path:
    b = tmp_path / "storyboard"
    (b / "grids").mkdir(parents=True)
    grid, panel = b / "grids" / "ep13_grid_x.png", b / "shot_00.png"
    for p, t in ((grid, grid_at), (panel, panel_at)):
        p.write_bytes(b"x")
        os.utime(p, (t, t))
    return b


def test_a_grid_newer_than_the_panels_is_a_refusal(tmp_path):
    assert step.redrawn_grids(board(tmp_path, grid_at=2000, panel_at=1000)) == ["ep13_grid_x.png"]


def test_panels_cut_after_their_grids_are_current(tmp_path):
    assert step.redrawn_grids(board(tmp_path, grid_at=1000, panel_at=2000)) == []
