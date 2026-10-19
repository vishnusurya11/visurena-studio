"""G-WARP is HARD on S alone (P07, ep01 2026-10-18): all eight ep01 hard fails were Se-only
(Se 3.2-5.0 against 3.0 with S -0.64..1.96).  Se is an advisory ('eye'); row() recomputes the
state from the numbers, so a stale stored `fail` stops being HARD.  Fixture: the real ep01
(S, Se, share) triples, copied from the 28 dq records."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from studio import warp_gate as wg

FIX = json.loads((Path(__file__).parent / "fixtures" / "ep01_replay" / "P07" / "dq_warp.json").read_text("utf-8"))


@pytest.mark.parametrize("s, se, share, state", [
    (-0.04, 4.16, 1.0, "eye"),      # ep01 T07
    (None, 3.5, 1.0, "eye"),
    (2.5, 3.5, 1.0, "eye"),         # S on the wall is not over it
    (2.6, 0.0, 1.0, "fail"),
    (2.6, 4.0, 1.0, "fail"),
    (1.2, 3.0, 1.0, "pass"),        # Se on its wall is not over it
    (1.8, 3.5, 1.0, "eye"),         # the eye advisory wins over a warn S
])
def test_only_s_over_the_wall_fails(s, se, share, state):
    assert wg.verdict(s, se, share) == state


def test_the_stored_t07_fail_is_ok_and_not_hard_through_row():
    g = wg.row({"state": "fail", "S": -0.04, "Se": 4.16, "share": 1.0, "spans": [[4, 4]]})
    assert g.ok and not g.hard and "eye" in g.note


def test_an_s_over_the_wall_is_a_hard_fail_whatever_the_stored_state():
    g = wg.row({"state": "pass", "S": 2.6, "Se": 0.0, "share": 1.0, "spans": []})
    assert not g.ok and g.hard


def test_the_eye_state_has_no_cure():
    assert wg.cure("eye", 0, 40.0) == "" and wg.cure("eye", 5, None) == ""


def test_all_ep01_triples_give_zero_hard_warp_rows():
    rows = [wg.row(v["warp"]) for v in FIX.values()]
    assert len(rows) == 28 and not [r for r in rows if r.hard and not r.ok]


def test_the_eight_se_only_fails_replay_as_advisories():
    states = {k: wg.verdict(v["warp"]["S"], v["warp"]["Se"], v["warp"]["share"]) for k, v in FIX.items() if v["warp"]}
    for t in ("T07", "T10", "T15", "T16", "T19", "T20", "T21", "T24"):
        assert states[t] in ("eye", "warn")


def test_a_blink_of_seven_frames_is_not_a_fail():
    rows = {"rf": [1.0] * 66 + [9.0] * 7, "rb": [0.0] * 73, "mf": [0.0] * 73, "re": [1.0] * 66 + [9.0] * 7}
    import numpy as np
    m = wg.judge({k: np.array(v, float) for k, v in rows.items()}, share=1.0, frames=74)
    assert m["state"] != "fail" and m["eye_spans"] == [[66, 72]]
