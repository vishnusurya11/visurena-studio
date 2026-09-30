"""A row that failed on the kept take AND on another attempt of the same take
repeated on a fresh seed: the judge marks it `repeated`, and no seed is spent
on it again -- a fresh seed already reproduced it.  A row that failed only now
is stochastic and may still ride a seed when no cause cure claims it first.

Recalibrated 2026-09-30 (five-expert debate): pass-through is an advisory now
(unbenched wall, ep14 T11 false alarm), so `dq_faults` no longer lifts it; the
repeated/fresh distinction is carried on `leak` (curable advisory) and
`cut-vote` (hard), and the seed-skip lives in the batched router's `cure_of`.
"""
from __future__ import annotations

import json
from pathlib import Path

from studio import take_ladder
from studio.judges import take_eye

ROWS = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "flow" / "take_dq_rows.json"


def gates() -> list[dict]:
    return json.loads(ROWS.read_text(encoding="utf-8"))["gates"]


def record() -> dict:
    """The kept T07 fails every row; the displaced attempt failed leak alone."""
    rows = gates()
    lost = [dict(g, ok=g["name"] != "leak") for g in rows]
    return {"file": "T07.mp4", "gates": rows,
            "attempts": [{"file": "T07_fail1.mp4", "gates": lost}, {"file": "T07.mp4", "gates": rows}]}


def test_the_repeated_row_is_marked_and_the_fresh_one_is_not():
    by = {f.kind: f for f in take_eye.dq_faults(7, record())}
    assert by["leak"].evidence["repeated"] is True
    assert by["cut-vote"].evidence["repeated"] is False
    assert by["leak"].where == "T07" and by["leak"].severity == "low"


def test_the_router_never_seeds_a_repeated_or_never_seed_row():
    by = {f.kind: f for f in take_eye.dq_faults(7, record())}
    assert not take_ladder.wants(by["leak"], "seed")                # NEVER_SEED
    assert take_ladder.wants(by["cut-vote"], "seed")                # fresh, so a seed COULD take it
    assert take_ladder.cure_of([by["cut-vote"]]) == "move_type"     # but the cause cure claims it first
    assert take_ladder.cure_of([by["leak"]]) == ""                  # uncovered leak: terminal, never a seed
    repeated = by["cut-vote"].model_copy(
        update={"kind": "shimmer", "evidence": {**by["cut-vote"].evidence, "repeated": True}})
    assert take_ladder.cure_of([repeated]) == ""                    # a fresh seed already reproduced it


def test_a_first_attempt_has_nothing_to_repeat():
    doc = {"file": "T07.mp4", "gates": gates(), "attempts": [{"file": "T07.mp4", "gates": gates()}]}
    assert all(f.evidence["repeated"] is False for f in take_eye.dq_faults(7, doc))
