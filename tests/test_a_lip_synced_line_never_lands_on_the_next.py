"""ep22 (2026-10-08 20:47Z): QC heard line 15 as 'Come nearer. Dog. Good dog.'
Line 14, the dialogue 'Good dog!', was laid 1.97 s late to meet its take's
soundtrack lag -- on top of line 15's narration in the same shot (74.72 s
against 73.45 s).  Two voices over each other is worse than a late mouth: a
line moved for lip-sync stops a breath before the next line, and never moves
earlier than planned."""
from __future__ import annotations

import json

from studio import line_laid

PLACED = {
    "shots": [{"index": 12, "t_start": 70.79, "t_end": 77.29}],
    "lines": [{"index": 14, "shot": 12, "kind": "dialogue", "at": 71.042, "seconds": 1.71},
              {"index": 15, "shot": 12, "kind": "narration", "at": 73.452, "seconds": 2.25}],
}


def _room(tmp_path, lag: float):
    (tmp_path / "T12.dq.json").write_text(json.dumps({"audio": {"mux_lag_s": lag}}), encoding="utf-8")
    return tmp_path


def test_a_lagged_line_stops_a_breath_before_the_next(tmp_path):
    laid = {l["index"]: l for l in line_laid.laid_lines(PLACED, _room(tmp_path, 1.97))}
    assert laid[14]["at"] + laid[14]["seconds"] <= laid[15]["at"] - line_laid.BREATH_S + 1e-6
    assert laid[14]["at"] >= 71.042                      # never earlier than planned
    assert laid[15]["at"] == 73.452                      # narration as planned


def test_a_small_lag_with_room_still_meets_its_take(tmp_path):
    laid = {l["index"]: l for l in line_laid.laid_lines(PLACED, _room(tmp_path, 0.30))}
    assert abs(laid[14]["at"] - 71.342) < 1e-6
