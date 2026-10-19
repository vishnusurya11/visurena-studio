"""One hole ruler (Jekyll Kawajiri ep01, C7): the G-HOLE gate and step 05's hold cure disagreed by
hundredths -- the cure trimmed a measured hole to 5.5 s, the re-time's frame rounding landed it at
5.53 s, and the gate refused the cure's own work (RUNLOG row 39).  speech_gap holds the ruler once:
the wall the cures AIM at (HOLE_WALL_S) and the slack under which the gate does not refuse
(HOLE_SLACK_S, the projected-vs-measured error, 0.04 s on ep17/ep18).  The fixture is ep01's own
measured placement, which carries a 5.53 s hole.
"""
from __future__ import annotations

import json
from pathlib import Path

from studio import plan_cures, plan_gates, speech_gap as sg

PLACED = Path(__file__).parent / "fixtures" / "ep01_replay" / "P02" / "placed.json"


def ep01_placed() -> dict:
    return json.loads(PLACED.read_text(encoding="utf-8"))


def test_the_wall_is_the_max_gap_less_the_margin():
    assert sg.HOLE_WALL_S == sg.MAX_GAP_S - sg.HOLE_MARGIN_S == 5.5


def test_ep01_measured_5_53_hole_is_over_the_cures_wall_but_not_over_the_gates():
    placed = ep01_placed()
    aimed = [round(e - s, 2) for s, e, _ in sg.holes(placed)]
    refused = [round(e - s, 2) for s, e, _ in sg.holes(placed, sg.HOLE_SLACK_S)]
    assert 5.53 in aimed and 5.53 not in refused


def test_a_hole_past_the_slack_is_still_refused():
    placed = ep01_placed()
    placed["lines"][-1]["at"] += 0.2
    assert sg.holes(placed, sg.HOLE_SLACK_S)


def test_the_gate_does_not_refuse_the_hole_the_cure_leaves(monkeypatch):
    monkeypatch.setattr(plan_gates, "projected_place", lambda episode, rate: ep01_placed())
    assert plan_gates.hole_faults(None, 2.45) == []


def test_the_gate_and_the_cures_read_the_one_wall():
    import inspect
    for fn in (plan_gates.hole_faults, plan_cures._close_projected_holes, plan_cures.trim_measured_holes):
        src = inspect.getsource(fn)
        assert "MAX_GAP_S - speech_gap.HOLE_MARGIN_S" not in src, fn.__name__
