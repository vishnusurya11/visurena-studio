"""Two cast designs are twins on ONE line: NEAREST_CEIL, the design-vs-design measure.

2026-10-21 review of the 16 kHz fix: `collisions()` (the cast run's COLLISION ... recast
printout) compared design-vs-design pairs with APART = SAME_SPEAKER (0.60), a line set from
LINES scored against designs.  On the new ruler it would have told the owner to recast
Lucy-Sawyer 0.697, Hyde-Lanyon 0.648 and five more pairs that the design gate
(`design_fault`, NEAREST_CEIL 0.75) accepts and whose lines still lead their cast.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("cast_twins", ROOT / "scripts" / "cast" / "cast_voices.py")
cast_voices = importlib.util.module_from_spec(spec)
sys.modules["cast_twins"] = cast_voices
spec.loader.exec_module(cast_voices)


def staged(tmp_path, monkeypatch, scores: dict) -> list[str]:
    cast = sorted({w for pair in scores for w in pair})
    for who in cast:
        room = tmp_path / "cast" / who / "voice"
        room.mkdir(parents=True)
        (room / "design.wav").write_bytes(b"x")
    monkeypatch.setattr(cast_voices.voice_ear, "apart", lambda clips: dict(scores))
    return cast


def test_a_pair_the_design_gate_accepts_is_no_collision(tmp_path, monkeypatch):
    cast = staged(tmp_path, monkeypatch, {("hyde", "lanyon"): 0.648, ("lucy", "sawyer"): 0.697})
    assert cast_voices.collisions(tmp_path, cast) == []


def test_a_pair_over_the_twin_line_is_a_collision(tmp_path, monkeypatch):
    over = cast_voices.NEAREST_CEIL + 0.01
    cast = staged(tmp_path, monkeypatch, {("hyde", "lanyon"): 0.648, ("lucy", "lucy_child"): over})
    assert cast_voices.collisions(tmp_path, cast) == [("lucy", "lucy_child", over)]
