"""A dialogue line is laid where its take's own soundtrack put it.

ep13 T11 (2026-09-27): MiniMax-H3 wrote the take's soundtrack 1.08 s after
the wav was laid and drove the mouth to THAT soundtrack; the master laid the
line at the planned time, so the voice finished before the lips moved (voice
76.2-77.6 s, mouth 77.5-79.7 s in master_iter1).  Every other ep13 dialogue
take measured 0.000 s and is laid exactly as before.
"""
import json

from studio import line_laid as assemble

LINE = {"index": 10, "kind": "dialogue", "shot": 11, "at": 76.083, "seconds": 1.84}


def test_a_late_soundtrack_moves_the_line_to_the_mouth():
    assert assemble.laid_at(LINE, lag=1.08, shot_end=79.875) == 77.163


def test_a_synced_take_keeps_the_planned_time():
    assert assemble.laid_at(LINE, lag=0.0, shot_end=79.875) == 76.083
    assert assemble.laid_at(LINE, lag=None, shot_end=79.875) == 76.083


def test_narration_is_never_moved():
    assert assemble.laid_at({**LINE, "kind": "narration"}, lag=1.08, shot_end=79.875) == 76.083


def test_the_line_never_runs_past_its_shot():
    assert assemble.laid_at(LINE, lag=3.0, shot_end=79.875) == round(79.875 - 1.84, 3)


def test_the_lines_are_laid_from_the_take_verdicts(tmp_path):
    (tmp_path / "T11.dq.json").write_text(json.dumps({"audio": {"mux_lag_s": 1.08}}), encoding="utf-8")
    placed = {"shots": [{"index": 11, "t_end": 79.875}], "lines": [LINE]}
    assert assemble.laid_lines(placed, tmp_path)[0]["at"] == 77.163
