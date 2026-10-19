"""Replay of the Jekyll Kawajiri ep01 dq records and take-eye verdict (fixtures are copies):
T08 passed its dq but the take eye read two faces as one man (facenet 0.79-0.94, frames 0-4) --
that never reached the cut log.  flagged_takes lifts it, high, with its seconds; T01, T07, T10,
T15, T16, T19, T20, T21 and T24 are listed beside it."""
from __future__ import annotations

import json
from pathlib import Path

from studio import dead_footage as dead

FIX = Path(__file__).parent / "fixtures" / "ep01_replay" / "P09"
KEPT = {1, 7, 8, 10, 15, 16, 19, 20, 21, 24}


def settled_faults():
    eye = json.loads((FIX / "eye_b368ae93.json").read_text(encoding="utf-8"))
    return [{**f, "evidence": {**f["evidence"], "settled": "keep_best"}} for f in eye["faults"]]


def records():
    return {i: json.loads((FIX / f"T{i:02d}.dq.json").read_text(encoding="utf-8")) for i in KEPT}


def flagged():
    order = [(i, 4.0 + (i == 21)) for i in range(28)]
    return dead.flagged_takes(order, {i: [i] for i, _ in order}, {21: 1.25}, records(), dead.lifted(settled_faults()))


def test_the_acceptance_set_is_listed():
    assert {r["take"] for r in flagged()} == KEPT


def test_the_clones_take_is_high_with_its_seconds():
    row = next(r for r in flagged() if r["take"] == 8)
    assert row["severity"] == "high" and "clones" in row["rows"] and row["seconds_in_master"] == 4.0
    assert any("facenet 0.943" in n for n in row["notes"])


def test_a_slowed_take_says_so():
    row = next(r for r in flagged() if r["take"] == 21)
    assert row["slowed"] is True and row["seconds_in_master"] == 5.0


def test_every_row_has_the_k7_keys():
    assert all(set(r) == {"take", "shot", "seconds_in_master", "slowed", "rows", "notes", "severity"}
               for r in flagged())


def test_a_take_cut_from_the_master_is_not_listed():
    order = [(i, 4.0) for i in range(28) if i != 8]
    out = dead.flagged_takes(order, {}, {}, records(), dead.lifted(settled_faults()))
    assert 8 not in {r["take"] for r in out}
