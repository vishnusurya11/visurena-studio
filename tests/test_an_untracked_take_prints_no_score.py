"""Under TRACKED_MIN the faces were barely found: S and Se are None in the record, S_raw is
kept, and the note never crashes on None (ep01 T17 printed S 32.77 at share 0.14)."""
from __future__ import annotations

import numpy as np

from studio import warp_gate as wg


def rows(n=8):
    return {"rf": np.full(n, 40.0), "rb": np.zeros(n), "mf": np.zeros(n), "re": np.full(n, 40.0)}


def test_an_untracked_take_records_no_score_but_keeps_the_raw_one():
    m = wg.judge(rows(), share=0.14, frames=9)
    assert m["state"] == "unmeasurable" and m["S"] is None and m["Se"] is None and m["S_raw"] > 30


def test_the_row_note_of_an_unscored_take_does_not_crash():
    g = wg.row({"state": "unmeasurable", "S": None, "Se": None, "share": 0.14, "spans": []})
    assert g.ok and "no score" in g.note


def test_a_tracked_take_keeps_its_scores():
    m = wg.judge(rows(), share=0.9, frames=9)
    assert m["S"] is not None and m["S_raw"] == m["S"]


def test_an_old_record_with_a_junk_score_prints_none_under_the_tracked_share():
    """ep01 T17 stored S 32.77 at share 0.14."""
    g = wg.row({"state": "unmeasurable", "S": 32.77, "Se": 27.61, "share": 0.14, "spans": []})
    assert "32.77" not in g.note and "no score" in g.note
