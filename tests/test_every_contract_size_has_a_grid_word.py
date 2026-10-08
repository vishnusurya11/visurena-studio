"""ep21 launch16 (2026-10-08 09:44Z): the signed plan sized shots 6, 20, 21
and 25 'full' -- a size the contract allows -- and grids.py died on KeyError
'full' two grids in, because its size-word table knew five of the seven sizes.
Every size the contract can sign is a size the grid can say."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import get_args

from studio.episode_spec import Size

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("grids_mod", ROOT / "scripts" / "episode" / "grids.py")
grids = importlib.util.module_from_spec(spec)
sys.modules["grids_mod"] = grids
spec.loader.exec_module(grids)


def test_every_contract_size_has_a_grid_word():
    missing = [s for s in get_args(Size) if s not in grids.SAID]
    assert missing == []


def test_every_contract_size_has_a_cut_clause():
    from studio import storyboard_grid as sg
    for size in get_args(Size):
        assert sg.cut_clause(size, peopled=True) and sg.cut_clause(size, peopled=False)


def test_the_full_shot_is_said_as_a_whole_figure():
    assert "FULL" in grids.SAID["full"]
    assert "CLOSE" in grids.SAID["extreme_close"]
