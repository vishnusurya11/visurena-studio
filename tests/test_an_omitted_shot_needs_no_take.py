"""ep27 (2026-10-10 22:15Z): the cut refused 'no take for shots [6, 8]' -- the
plan OMITS shots 6 and 8 (a passage kept out of the picture), the timeline
places neither and the take builder renders neither, but the cut's take check
counted every plan shot.  A shot the cut omits needs no take."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("ep_assemble_omit", ROOT / "scripts" / "episode" / "assemble.py")
assemble = importlib.util.module_from_spec(spec)
sys.modules["ep_assemble_omit"] = assemble
spec.loader.exec_module(assemble)


def _episode(omit):
    return SimpleNamespace(shots=[SimpleNamespace(index=i) for i in range(4)], omit=omit)


def test_an_omitted_shot_is_not_missing():
    takes = {0: SimpleNamespace(shots=[0]), 1: SimpleNamespace(shots=[1]), 3: SimpleNamespace(shots=[3])}
    assert assemble.shots_without_takes(_episode([2]), takes) == []


def test_a_shot_the_cut_keeps_still_needs_its_take():
    takes = {0: SimpleNamespace(shots=[0]), 1: SimpleNamespace(shots=[1])}
    assert assemble.shots_without_takes(_episode([2]), takes) == [3]
