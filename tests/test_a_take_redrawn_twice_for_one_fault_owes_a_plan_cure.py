"""A take re-drawn twice for the same fault is not drawn a third time; the plan owes the cure (craft ruling A24).

Jekyll ep01 T01's gait fault was drawn 10 times over 7 runs: `MAX_TAKE_ATTEMPTS` counts archived draws in one
room, and a relaunch, a repair or a cleared attempts/ folder started it again.  Now each batched round books one
draw per fault kind per kept take in the episode's attempts.json (`fault.T01.gait`), which every run reads; at
REPEAT_CAP (2) the router sends that take no render cure (a free cure still runs), the terminal keeps the best
draw, and one "plan cure owed: shot N motion" row is written to cures_owed.jsonl.  Routing the owed row to an
automatic plan edit is T24, not built here."""
from __future__ import annotations

import json
from types import SimpleNamespace

from studio import step_attempts, take_ladder as tl
from studio.judges.verdict import Fault, Verdict


def room_of(tmp_path):
    room = tmp_path / "ep01" / "takes" / "r2v"
    room.mkdir(parents=True)
    (room / "shots.json").write_text(json.dumps([{"index": 1, "shots": [1]}, {"index": 2, "shots": [2, 3]}]),
                                     encoding="utf-8")
    return room


def verdict(*faults: Fault) -> Verdict:
    return Verdict(judge="take_eye", version="1", passed=False, confidence=1.0, faults=list(faults))


GAIT = Fault(kind="gait", where="T01", note="shuffle: 4.1 steps/s HARD")


def drawn(room, index: int, kind: str, times: int) -> None:
    for _ in range(times):
        step_attempts.spend(room.parent.parent, tl.fault_key(index, kind))


def test_one_same_fault_draw_still_routes(tmp_path):
    room = room_of(tmp_path)
    drawn(room, 1, "gait", 1)
    assert 1 in tl.route(verdict(GAIT), room).get("gait_verb", {})


def test_the_third_same_fault_draw_is_refused(tmp_path):
    room = room_of(tmp_path)
    drawn(room, 1, "gait", 2)
    routed = tl.route(verdict(GAIT), room)
    assert not any(1 in routed.get(cure, {}) for cure in tl.DRAWS)


def test_a_free_cure_is_never_capped(tmp_path):
    room = room_of(tmp_path)
    drawn(room, 1, "leak", 2)
    leak = Fault(kind="leak", where="T01", note="plate", evidence={"hard": True, "covers": True})
    assert 1 in tl.route(verdict(leak), room).get("head_cut", {})


def test_the_refused_take_owes_one_plan_cure_row(tmp_path):
    room = room_of(tmp_path)
    drawn(room, 1, "gait", 2)
    tl.owe_plan_cures(room, verdict(GAIT))
    tl.owe_plan_cures(room, verdict(GAIT))
    rows = [json.loads(l) for l in (room.parent.parent / tl.OWED).read_text(encoding="utf-8").splitlines()]
    assert [r["row"] for r in rows] == ["plan cure owed: shot 1 motion"]
    assert rows[0]["fault"] == "gait" and rows[0]["draws"] == 2


def test_a_round_books_each_kept_takes_fault_kinds(tmp_path, monkeypatch):
    room = room_of(tmp_path)
    monkeypatch.setattr(tl, "retake", lambda *a, **k: None)
    ctx = SimpleNamespace(home=room.parent.parent)
    for _ in range(2):
        tl.render_round(ctx, SimpleNamespace(name="EYE_TAKES"), {1: [GAIT]}, [], "--flag", verdict(GAIT), room)
    assert step_attempts.count(room.parent.parent, tl.fault_key(1, "gait")) == 2
    assert tl.route(verdict(GAIT), room) == {}
