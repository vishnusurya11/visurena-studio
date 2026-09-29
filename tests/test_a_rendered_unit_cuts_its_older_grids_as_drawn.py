"""ep14 (2026-09-29): a grid-prompt fix made every drawn grid read as stale, and
panels.py would have refused the whole board of a unit whose 30 takes were
already rendered -- blocking the two panels the fix was redrawn for.  A unit
that has takes cuts its older grids as drawn (the board's own report-mode rule,
step 07); an unshot unit still refuses them."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "episode"))

import panels  # noqa: E402


def test_an_unshot_unit_refuses_a_stale_grid(tmp_path):
    assert panels.stale_refusal(["ep14_grid_yard_3x1"], tmp_path) is not None


def test_a_shot_unit_cuts_it_as_drawn(tmp_path):
    take = tmp_path / "takes" / "r2v" / "T00.mp4"
    take.parent.mkdir(parents=True)
    take.write_bytes(b"take")
    assert panels.stale_refusal(["ep14_grid_yard_3x1"], tmp_path) is None


def test_no_stale_grid_is_no_refusal(tmp_path):
    assert panels.stale_refusal([], tmp_path) is None
