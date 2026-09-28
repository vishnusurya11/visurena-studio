"""A lag follows the take's LENGTH, not its seed (measured twice: a fresh seed
moved the lag 0.05 s; a shorter take passed).  The mouth's lag row and the mux
lip-sync row both go straight to the shorter take, and the seed rung never
sees them."""
from __future__ import annotations

import json
from pathlib import Path

from studio import take_ladder
from studio.judges import take_eye

ROWS = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "flow" / "take_dq_rows.json"


def lagging() -> dict:
    rows = json.loads(ROWS.read_text(encoding="utf-8"))["gates"]
    mux = {"name": "lip-sync", "value": 0.56, "ok": False, "hard": True, "note": "mux lag +0.560s", "penalty": 40.0}
    return {"file": "T05.mp4", "gates": [g for g in rows if g["name"] == "lag"] + [mux], "attempts": []}


def test_the_advisory_lag_row_is_points_off_not_a_fault():
    """MEASURED on ep13 (2026-09-27, finding 61): five shorter_take rounds on
    advisory lag rows (T00 -6..-8 f, T11 +19 f) cost 157 min and cured none --
    every T00 attempt already passed.  The HARD lip-sync row still climbs."""
    by = {f.kind: f for f in take_eye.dq_faults(5, lagging())}
    assert "lag" not in by
    assert by["lip-sync"].severity == "normal"


def test_the_lip_sync_row_takes_the_shorter_take_never_a_seed():
    for fault in take_eye.dq_faults(5, lagging()):
        assert not take_ladder.wants(fault, "seed", "The camera holds a locked-off frame; he speaks")
        assert take_ladder.wants(fault, "shorter_take", "")
        assert not take_ladder.wants(fault, "move_type", "")
