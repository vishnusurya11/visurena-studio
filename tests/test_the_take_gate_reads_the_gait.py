"""The take gate carries G-GAIT (studio/gait.py): a shuffling walker fails the take
HARD, a take whose plan walks nobody reads `n/a by the plan` and is never decoded
for it (Jekyll HEL ep01 T03, owner 2026-10-14)."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "episode"))
import take_dq  # noqa: E402

WALKER = "The camera pans across; the little man stumps along the far pavement at a good walk"
SHUFFLE = {"state": "shuffle", "freq": 3.94, "step_h": 0.032, "travel_hps": 0.13}


def test_the_last_judged_row_is_the_gait():
    rec = {"lane": "narration", "motion": WALKER, "motions": [WALKER]}
    rows = take_dq.judge_rows({"gait": SHUFFLE}, rec)
    assert rows[-1].name == "gait"
    assert rows[-1].hard and not rows[-1].ok


def test_a_take_with_no_walker_is_never_decoded_for_the_gait():
    called = []
    got = take_dq.gait_measure([np.zeros((8, 8, 3), np.uint8)] * 30, {"motions": ["he lifts his hand"]},
                               lambda rgb: called.append(1) or [])
    assert got == {"gait": None} and called == []


def test_a_walker_take_is_measured():
    got = take_dq.gait_measure([np.zeros((8, 8, 3), np.uint8)] * 6, {"motions": [WALKER]}, lambda rgb: [])
    assert got["gait"]["state"].startswith("unmeasured")
