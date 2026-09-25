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


def test_the_advisory_lag_row_is_a_low_fault_the_ladder_can_cure():
    by = {f.kind: f for f in take_eye.dq_faults(5, lagging())}
    assert by["lag"].severity == "low" and by["lag"].evidence["value"] == 3
    assert by["lip-sync"].severity == "normal"


def test_neither_lag_row_takes_a_seed_and_both_take_the_shorter_take():
    for fault in take_eye.dq_faults(5, lagging()):
        assert not take_ladder.wants(fault, "seed", "The camera holds a locked-off frame; he speaks")
        assert take_ladder.wants(fault, "shorter_take", "")
        assert not take_ladder.wants(fault, "move_type", "")
