"""A take's late soundtrack the edit lays within its shot is not a lip fault.

ep13 T11 (2026-09-27): the mux lag gate failed T11 at +1.08 s through every
rung; the edit now lays the line where the take spoke it (studio/line_laid),
and the master was checked in sync by eye.  A lag the shot has no room for,
or a line that mis-speaks, still fails.
"""
import importlib.util
import sys
from pathlib import Path

from studio import take_verdict as tv

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("take_dq_room", ROOT / "scripts/episode/take_dq.py")


def gate(lag, room, heard="Have you any water?"):
    return tv.lip_gate("dialogue", {"mux_lag_s": lag, "room_s": room, "heard": heard}, "Have you any water?")


def test_a_lag_the_shot_has_room_for_passes_with_a_note():
    g = gate(1.08, 1.95)
    assert g.ok and "laid by the edit" in g.note and g.penalty == 0.0


def test_a_lag_past_the_shot_still_fails():
    assert not gate(1.08, 0.5).ok


def test_without_a_room_the_old_wall_stands():
    assert not gate(1.08, None).ok and gate(0.0, None).ok


def test_the_room_is_the_shot_end_after_the_dialogue_line():
    take_dq = importlib.util.module_from_spec(_spec)
    sys.modules["take_dq_room"] = take_dq
    _spec.loader.exec_module(take_dq)
    placed = {"shots": [{"index": 11, "t_end": 79.875}],
              "lines": [{"shot": 11, "kind": "dialogue", "at": 76.083, "seconds": 1.84}]}
    assert take_dq.line_room(placed, {"index": 11, "shots": [11]}) == 1.952
    assert take_dq.line_room(placed, {"index": 12, "shots": [12]}) is None
