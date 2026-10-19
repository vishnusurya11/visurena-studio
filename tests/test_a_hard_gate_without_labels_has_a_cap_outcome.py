"""A HARD gate fitted with no owner labels states what happens at the cap (P16).

G-WARP read "HARD on fail ... Fitted on 27 clips, NO owner labels" with no outcome beside it; on
Jekyll Kawajiri ep01 it failed 8 takes on Se alone, two retake rounds changed nothing, and the
policy that followed (keep_best, ship flagged) was written nowhere.
"""
from __future__ import annotations

from pathlib import Path

GATES = Path(__file__).resolve().parents[1] / ".claude" / "skills" / "episode" / "GATES.md"


def unlabelled_rows() -> list[str]:
    rows = [l for l in GATES.read_text(encoding="utf-8").splitlines() if l.startswith("|")]
    return [r for r in rows if "no owner labels" in r.lower()]


def test_there_is_an_unlabelled_row_to_judge():
    assert any("G-WARP" in r for r in unlabelled_rows())


def test_every_unlabelled_row_states_its_outcome_at_the_cap():
    assert [r[:40] for r in unlabelled_rows() if "at the cap" not in r.lower()] == []
