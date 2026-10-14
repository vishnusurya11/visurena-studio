"""Dialogue is locked or over the shoulder by default (Jekyll ep01 motion review,
2026-10-13): 6 of 8 dialogue shots pushed in and every exchange ended on the
same face-filling close.  The catalog says locked-off is the sharpest move and
the best for lips; three rules steered away from it:

- G-MOVES refused the same move twice running and capped any move at a
  quarter of the shots, so a shot/reverse-shot exchange could not stay locked;
- the retake ladder turned a frozen locked take into `push_slow`;
- the take builder's refusal gave the writer a push as its only example.

Now a dialogue run counts as one shot/reverse-shot unit, a frozen dialogue
take gives the ACTOR a verb, and G-TALK allows one travelling dialogue shot
(WotW ep01-03, the liked ones, push on 1, 0, 0).  $0."""
from __future__ import annotations

import inspect
from types import SimpleNamespace

from studio import plan_gates, take_ladder

LOCKED = "The camera holds a locked-off frame across the whole shot; he speaks; his hand lifts"
OTS = "Over the shoulder of the listener, the camera holds across the whole shot; he speaks; he nods"
PUSH = "The camera pushes in toward his face across the whole shot; he speaks; his hand lifts"
MOVES = ["The camera pans across to the gate; he walks; the gate swings",
         "The camera tracks sideways to the right, past the wall; he walks; the dog runs",
         "The camera rises above the yard, looking down over the place; he runs; the cart rolls",
         "The camera pulls back from the cart, widening to show the place around it; he runs; the cart rolls",
         "The camera tilts up from the ground to the roof; the boy climbs; the slate slides",
         "The camera tracks beside the man; he walks; his coat swings",
         "The camera orbits the well; the woman draws water; the rope runs",
         "The camera pushes in toward the lamp; his hand turns the wick; the flame rises"]


def _ep(motions: list[str], dialogue: set[int]):
    shots = [SimpleNamespace(index=i, motion=m, camera="", still=False) for i, m in enumerate(motions)]
    lines = [SimpleNamespace(index=i, shot=i, kind="dialogue" if i in dialogue else "narration")
             for i in range(len(motions))]
    return SimpleNamespace(shots=shots, lines=lines)


def test_a_locked_exchange_is_not_a_repeated_move():
    ep = _ep(MOVES[:4] + [LOCKED, OTS, LOCKED, LOCKED] + MOVES[4:], dialogue={4, 5, 6, 7})
    assert not [f for f in plan_gates.moves_faults(ep) if "twice running" in f or "share" in f]


def test_holding_the_dialogue_never_raises_another_moves_share():
    """The replay of shipped WotW ep04 (2026-10-13): taking held dialogue shots out
    of the DENOMINATOR lifted 'high_angle' from 0.25 to 0.32 -- a new refusal.
    Held dialogue leaves the count, never the shot total."""
    pan = "The camera pans across to the gate; he walks; the gate swings"
    ep = _ep([pan, LOCKED, pan, LOCKED, MOVES[1], MOVES[2], MOVES[3], LOCKED, MOVES[4], MOVES[5], MOVES[6], MOVES[7]],
             dialogue={1, 3, 7})
    assert not [f for f in plan_gates.moves_faults(ep) if "share" in f]


def test_two_locked_narration_shots_running_are_still_refused():
    ep = _ep(MOVES[:4] + [LOCKED, LOCKED] + MOVES[4:], dialogue=set())
    assert [f for f in plan_gates.moves_faults(ep) if "twice running" in f]


def test_a_held_angle_on_a_spoken_line_is_not_still():
    shot = SimpleNamespace(index=0, motion=LOCKED, camera="a low angle at knee height", still=False)
    assert plan_gates.still_fault(shot) is not None
    assert plan_gates.still_fault(shot, dialogue=True) is None


def test_g_talk_allows_one_travelling_dialogue_shot():
    ep = _ep([PUSH, LOCKED, OTS, PUSH, PUSH], dialogue={0, 1, 2, 3, 4})
    got = plan_gates.talk_faults(ep)
    assert [g.split(":")[0] for g in got] == ["G-TALK shot 0", "G-TALK shot 3", "G-TALK shot 4"]
    assert plan_gates.talk_faults(_ep([PUSH, LOCKED, OTS], dialogue={0, 1, 2})) == []


def test_a_pan_or_a_tilt_on_a_spoken_line_is_not_a_travel():
    """WotW ep01, which the owner liked, pans on all four of its dialogue shots:
    the camera turns where it stands; only a camera that TRAVELS counts."""
    pan = "The camera pans across to his face; he speaks; his hand lifts"
    assert plan_gates.talk_faults(_ep([pan, pan, pan, PUSH], dialogue={0, 1, 2, 3})) == []


def test_a_frozen_dialogue_take_gives_the_actor_a_verb_never_a_push():
    motion = take_ladder.substitute("frozen-whole", LOCKED, "his face a third of the frame", dialogue=True)
    assert plan_gates.move_id(motion, "") == "locked"
    assert take_ladder.ACTOR_VERB in motion
    assert plan_gates.move_id(take_ladder.substitute("frozen-whole", LOCKED, "the lamp"), "") == "push_slow"


def test_the_take_builder_never_offers_a_push_as_its_example():
    from scripts.episode import takes_r2v
    src = inspect.getsource(takes_r2v.refuse_still_motions)
    assert "pushes in" not in src and "locked-off" in src


def test_the_battery_and_the_brief_carry_g_talk(tmp_path):
    from scripts.episode import plan_check
    from studio import plan_brief
    assert plan_check.talk_gate(_ep([PUSH, PUSH, LOCKED], dialogue={0, 1, 2}), tmp_path, 3) == 2
    assert any("G-TALK" in rule for rule in plan_brief.PICTURE_RULES)


def test_a_dialogue_take_frozen_again_with_the_actors_verb_pans():
    """Jekyll ep01 (HEL, 2026-10-14): T01 and T14 were locked with the actor's verb and
    froze again (92 % and 86 % static, runs 4.3 s and 3.6 s) -- the same fault on a fresh
    seed is the plan's.  The next move is a pan to the speaker: it turns where it stands,
    so G-TALK still holds (WotW ep01 panned all four spoken shots and was liked)."""
    once = take_ladder.substitute("frozen-whole", LOCKED, "his face a third of the frame", dialogue=True)
    twice = take_ladder.substitute("frozen-whole", once, "his face a third of the frame", dialogue=True)
    assert plan_gates.move_id(twice, "") == "pan_to"
    assert twice.count(take_ladder.ACTOR_VERB) == 1
    assert plan_gates.talk_faults(_ep([twice, twice, twice], dialogue={0, 1, 2})) == []
