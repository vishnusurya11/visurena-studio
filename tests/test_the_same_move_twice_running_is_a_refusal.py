"""G-MOVES: the same catalog move never on two consecutive shots."""
from types import SimpleNamespace

from studio import plan_gates as pg


def plan(heads: list[str]):
    return SimpleNamespace(shots=[SimpleNamespace(index=i, motion=h + "; his hand lifts; his head turns", camera="")
                                  for i, h in enumerate(heads)])


def test_two_pushes_running_are_named_by_shot():
    heads = ["pans from the lamp to the door", "pushes in on the face", "pushes in on the hand",
             "tilts up from the boots to the face"]
    got = [f for f in pg.moves_faults(plan(heads)) if "running" in f]
    assert got == ["G-MOVES shot 2: 'push_slow' follows the same move on shot 1 (twice running), "
                   "measured 2 against 1"]


def test_a_push_and_a_pull_running_are_different_moves():
    heads = ["pushes in on the face", "pulls back from the face", "pushes in on the hand"]
    assert not [f for f in pg.moves_faults(plan(heads)) if "running" in f]


def test_two_locked_frames_at_different_angles_are_different_moves():
    shots = [SimpleNamespace(index=0, motion="holds a locked-off frame; he writes; his head lifts",
                             camera="level with his eyes"),
             SimpleNamespace(index=1, motion="holds a locked-off frame; he writes; his head lifts",
                             camera="at knee height looking up at him, a low angle")]
    assert not [f for f in pg.moves_faults(SimpleNamespace(shots=shots)) if "running" in f]
