"""ep16 shot 19 (2026-10-02): a WIDE naming only Miss Elphinstone drew all four
poses of her turnaround sheet as four women -- twice, the second time with the
prompt saying 'that one person appears exactly once'.  Words do not beat a
staged picture.  A person who is only ever WIDE/FULL in a grid is therefore
not staged by sheet: at that size the face is a few pixels and the wardrobe
words carry her (the take still binds the sheet at render).  A person in any
closer panel of the grid keeps the sheet."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("grids", ROOT / "scripts" / "episode" / "grids.py")
grids = importlib.util.module_from_spec(spec)
sys.modules["grids"] = grids
spec.loader.exec_module(grids)


def shot(size, faces):
    return SimpleNamespace(size=size, faces=faces)


def test_only_wide_means_words_not_sheet():
    assert grids.wide_only("miss", [shot("wide", ["miss"])]) is True
    assert grids.wide_only("miss", [shot("full", ["miss"]), shot("wide", ["miss"])]) is True


def test_any_closer_panel_keeps_the_sheet():
    assert grids.wide_only("miss", [shot("wide", ["miss"]), shot("medium", ["miss"])]) is False
    assert grids.wide_only("miss", [shot("close", ["miss"])]) is False
