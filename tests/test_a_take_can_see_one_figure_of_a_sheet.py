"""ep16 attempt 4 (2026-10-02): the storyboard panels were clean, yet take T12
put two copies of Mrs. Elphinstone in the background -- white dress, straw
hat, brown bag: her sheet's other poses, placed as people.  Takes can stage
the same one-figure crop the grids do (studio.sheet_front); a sheet with no
crop falls back to the whole sheet."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("tr", ROOT / "scripts" / "episode" / "takes_r2v.py")
tr = importlib.util.module_from_spec(spec)
sys.modules["tr"] = tr
spec.loader.exec_module(tr)


def test_the_front_crop_replaces_the_sheet_when_it_exists(tmp_path):
    sheet = tmp_path / "sheet.png"
    sheet.write_bytes(b"x")
    assert tr.one_figure(sheet) == sheet                 # no crop yet: the whole sheet
    front = tmp_path / "sheet_front.png"
    front.write_bytes(b"y")
    assert tr.one_figure(sheet) == front                 # crop present: one figure
    other = tmp_path / "plate.png"
    other.write_bytes(b"z")
    assert tr.one_figure(other) == other                 # only sheets are swapped
