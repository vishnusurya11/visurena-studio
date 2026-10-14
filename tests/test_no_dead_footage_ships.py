"""G-DEAD: no dead footage in a master that ships.

Jekyll ep01 (2026-10-13, MOTION.md cause 3): 50.8 s of 173.5 (29 %) was near
dead -- shots 4 and 14 were still panels held 6+ s on a 1.06x zoompan, T04, T06
and T15 FAILED the take gate and shipped anyway (qc: "fail: T04 T06 T15", the
master passed), and two dead runs sat back to back (14 still, then 15 frozen).

The rule: no still held past STILL_LIMIT_S, no failed take, never two
near-dead shots in a row.  The CURE is free and $0 -- the dead shot leaves the
cut and its live neighbours cover its seconds, slowed at most MAX_STRETCH --
so a spent clock can still keep it; a dialogue shot is never cut or slowed
(its lips), and what no cut can cure refuses the master: a retake, never a
flagged ship.
"""
from __future__ import annotations

from studio import dead_footage as dead


def rec(passed=True, static=0.1):
    return {"passed": passed, "gates": [{"name": "frozen-whole", "value": static}]}


def test_the_states():
    assert dead.state_of(4, {4: "p"}, rec()) == "still"
    assert dead.state_of(6, {}, rec(passed=False)) == "failed"
    assert dead.state_of(19, {}, rec(static=0.63)) == "near_dead"
    assert dead.state_of(2, {}, rec()) == "alive"
    assert dead.state_of(2, {}, None) == "alive"


def test_a_short_still_is_allowed_a_long_one_is_dead():
    assert not dead.is_dead("still", dead.STILL_LIMIT_S)
    assert dead.is_dead("still", 6.4)
    assert dead.is_dead("failed", 1.0) and not dead.is_dead("near_dead", 9.0)


def test_near_dead_never_makes_a_dead_run():
    """WotW ep01 T00+T01, owner-liked, both 1.00 static (Mars in space)."""
    assert dead.faults([(0, 8.0), (1, 8.0)], {0: "near_dead", 1: "near_dead"}) == []
    assert dead.faults([(0, 2.0), (1, 8.0)], {0: "still", 1: "failed"})


def test_the_faults_name_every_kind():
    order = [(13, 6.0), (14, 6.4), (15, 6.0), (16, 6.0)]
    states = {13: "alive", 14: "still", 15: "failed", 16: "alive"}
    said = " ".join(dead.faults(order, states))
    assert "T14" in said and "T15" in said and "in a row" in said


def test_a_dead_shot_is_cut_and_its_neighbours_cover_it():
    order = [(3, 6.0), (4, 3.0), (5, 6.0)]
    states = {3: "alive", 4: "failed", 5: "alive"}
    room = {3: 6.3, 4: 6.0, 5: 6.3}
    plan = dead.cut_plan(order, states, room, dialogue=set())
    assert plan["cut"] == [4]
    assert plan["seconds"] == {3: 7.5, 5: 7.5}
    assert sum(s for _, s in dead.apply(order, plan)) == 15.0


def test_never_cut_or_stretch_a_dialogue_shot():
    order = [(3, 6.0), (4, 3.0), (5, 6.0)]
    states = {3: "alive", 4: "failed", 5: "alive"}
    room = {3: 6.3, 4: 6.0, 5: 6.3}
    assert dead.cut_plan(order, states, room, dialogue={4})["cut"] == []
    plan = dead.cut_plan(order, states, room, dialogue={3})
    assert plan["cut"] == [4] and plan["seconds"] == {5: 9.0}


def test_a_cut_too_long_for_its_neighbours_is_left_for_a_retake():
    order = [(3, 4.0), (4, 8.0), (5, 4.0)]
    states = {3: "alive", 4: "failed", 5: "alive"}
    plan = dead.cut_plan(order, states, {3: 4.2, 4: 8.0, 5: 4.2}, dialogue=set())
    assert plan["cut"] == []


def test_the_stretch_of_a_covered_neighbour():
    assert dead.stretch(7.5, 6.3) == round(7.5 / 6.3, 4)
    assert dead.stretch(5.0, 6.3) == 1.0


def test_jekyll_ep01_could_not_be_cut_so_it_is_refused():
    """The shipped cut: 14 still + 15 failed back to back; 4 still beside dialogue 5;
    6 a failed dialogue take.  No neighbour can cover 6.4 s at 1.5x, so the free cure
    cuts nothing and every fault stands: the master is refused and the ladder retakes."""
    order = [(i, 6.4) for i in range(17)]
    states = {i: "alive" for i in range(17)} | {4: "still", 6: "failed", 14: "still", 15: "failed"}
    plan = dead.cut_plan(order, states, {i: 6.8 for i in range(17)}, dialogue={5, 6, 13})
    left = " ".join(dead.faults(dead.apply(order, plan), states))
    assert plan["cut"] == []
    assert all(f"T{i:02d}" in left for i in (4, 6, 14, 15)) and "in a row" in left


# ---- the seat in assemble ---------------------------------------------------------

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("assemble_dead", ROOT / "scripts" / "episode" / "assemble.py")
assemble = importlib.util.module_from_spec(_spec)
sys.modules["assemble_dead"] = assemble
_spec.loader.exec_module(assemble)


def placed3(lines=None):
    return {"shots": [{"index": i, "seconds": s} for i, s in ((3, 6.0), (4, 3.0), (5, 6.0))],
            "lines": lines or [{"shot": 5, "kind": "narration"}]}


def write_dq(room: Path, index: int, passed: bool) -> None:
    (room / f"T{index:02d}.dq.json").write_text(json.dumps({"passed": passed, "gates": []}), encoding="utf-8")


def test_assemble_cuts_a_failed_take_its_neighbours_can_cover(tmp_path, monkeypatch):
    monkeypatch.setattr(assemble, "clip_seconds", lambda p: 6.3)
    for i, ok in ((3, True), (4, False), (5, True)):
        write_dq(tmp_path, i, ok)
    plan = assemble.dead_plan(placed3(), {3: "a", 4: "b", 5: "c"}, {}, tmp_path, {})
    assert plan["cut"] == [4] and plan["seconds"] == {3: 7.5, 5: 7.5}


def test_assemble_refuses_what_it_cannot_cut(tmp_path, monkeypatch):
    monkeypatch.setattr(assemble, "clip_seconds", lambda p: 6.3)
    for i, ok in ((3, True), (4, False), (5, True)):
        write_dq(tmp_path, i, ok)
    with pytest.raises(SystemExit, match="G-DEAD"):
        assemble.dead_plan(placed3([{"shot": 4, "kind": "dialogue"}]), {3: "a", 4: "b", 5: "c"}, {}, tmp_path, {})


def test_a_covering_take_plays_slower(tmp_path, monkeypatch):
    seen = []
    monkeypatch.setattr(assemble, "guard", lambda take, seconds, work: "")
    monkeypatch.setattr(assemble, "extract", lambda *a, **k: seen.append(k.get("pre")) or a[3])
    assemble.segment(3, 7.5, {3: Path("T03.mp4")}, {}, {}, tmp_path, {}, slow=1.1905)
    assert seen == ["setpts=1.1905*PTS"]
