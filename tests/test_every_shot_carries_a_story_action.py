"""G-ACTION (Jekyll ep01 review, 2026-10-13): 7 of 27 shots were empty sets whose
only movers were weather -- "a light wind lifts the flakes", "pigeons shuffle",
"smoke curls" -- 47 s of the picture.  WotW's faceless shots are EVENTS (the
flash, the cylinder, the lid turning, a hand on the lantern).  MEASURED with
this detector over every shipped plan: WotW 0-2 per episode, Scarlet 0-1,
Jekyll ep01 7 (exactly the seven the motion review named).  $0."""
from __future__ import annotations

from types import SimpleNamespace

from studio import plan_cures, plan_gates

HEAD = "The camera holds a locked-off frame across the whole shot"


def _shot(i, acts, faces=(), extras=0):
    return SimpleNamespace(index=i, faces=list(faces), extras=extras, cuts=[],
                           motion="; ".join([HEAD] + list(acts)))


def test_a_weather_clause_is_ambient_and_an_act_is_not():
    assert plan_gates.ambient_clause("a light wind lifts the flakes of peeling paint along the moulding")
    assert plan_gates.ambient_clause("pigeons shuffle along the gable ledge at the top")
    assert plan_gates.ambient_clause("grey smoke rises from the chimney pot")
    assert not plan_gates.ambient_clause("the whole crusted lid turns on its body")
    assert not plan_gates.ambient_clause("his hand turns the wick up and lifts the lantern")


def test_an_empty_shot_moved_only_by_weather_is_filler():
    assert plan_gates.filler_shot(_shot(0, ["a light wind stirs the awning", "pigeons shuffle on the ledge"]))
    assert not plan_gates.filler_shot(_shot(0, ["the red planet turns on its axis", "a pale haze shimmers"]))
    assert not plan_gates.filler_shot(_shot(0, ["a light wind stirs the awning"], faces=["lead"]))
    assert not plan_gates.filler_shot(_shot(0, ["a light wind stirs the awning"], extras=2))


def test_more_than_two_filler_shots_are_refused_each_by_name():
    shots = [_shot(i, ["a frost wind stirs a sheet of newspaper"]) for i in range(3)]
    shots.append(_shot(3, ["the man walks into the frame"], faces=["lead"]))
    got = plan_gates.action_faults(SimpleNamespace(shots=shots))
    assert [g.split(":")[0] for g in got] == ["G-ACTION shot 0", "G-ACTION shot 1", "G-ACTION shot 2"]
    assert plan_cures.cure_for(got[0]) is None                 # a story act is the writer's


def test_two_filler_shots_pass():
    shots = [_shot(i, ["a frost wind stirs a sheet of newspaper"]) for i in range(2)]
    assert plan_gates.action_faults(SimpleNamespace(shots=shots)) == []


def test_the_battery_counts_g_action_hard(tmp_path):
    from scripts.episode import plan_check
    shots = [_shot(i, ["a frost wind stirs a sheet of newspaper"]) for i in range(3)]
    assert plan_check.action_gate(SimpleNamespace(shots=shots)) == 3
