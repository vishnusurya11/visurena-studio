"""A row that failed on the kept take AND on another attempt of the same take
repeated on a fresh seed: the judge marks it `repeated`, and the seed rung
passes it by.  A row that failed only now is stochastic and gets its seed."""
from __future__ import annotations

import json
from pathlib import Path

from studio import take_ladder
from studio.judges import take_eye

ROWS = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "flow" / "take_dq_rows.json"


def gates() -> list[dict]:
    return json.loads(ROWS.read_text(encoding="utf-8"))["gates"]


def record() -> dict:
    """The kept T07 fails pass-through and cut-vote; the displaced attempt
    failed pass-through alone."""
    rows = gates()
    lost = [dict(g, ok=g["name"] != "pass-through") for g in rows]
    return {"file": "T07.mp4", "gates": rows,
            "attempts": [{"file": "T07_fail1.mp4", "gates": lost}, {"file": "T07.mp4", "gates": rows}]}


def test_the_repeated_row_is_marked_and_the_fresh_one_is_not():
    by = {f.kind: f for f in take_eye.dq_faults(7, record())}
    assert by["pass-through"].evidence["repeated"] is True
    assert by["cut-vote"].evidence["repeated"] is False
    assert by["pass-through"].where == "T07" and by["pass-through"].severity == "normal"


def test_the_seed_rung_skips_the_repeated_row_and_the_cause_rung_takes_it():
    by = {f.kind: f for f in take_eye.dq_faults(7, record())}
    moving = "The camera tracks sideways to the right along the fence; he holds the basket out"
    assert not take_ladder.wants(by["pass-through"], "seed", moving)
    assert take_ladder.wants(by["pass-through"], "move_type", moving)
    assert take_ladder.wants(by["cut-vote"], "seed", moving)


def test_a_first_attempt_has_nothing_to_repeat():
    doc = {"file": "T07.mp4", "gates": gates(), "attempts": [{"file": "T07.mp4", "gates": gates()}]}
    assert all(f.evidence["repeated"] is False for f in take_eye.dq_faults(7, doc))
