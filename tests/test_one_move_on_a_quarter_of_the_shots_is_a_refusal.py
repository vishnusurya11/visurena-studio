"""G-MOVES: no single move on more than a quarter of the plan's shots.

Calibrated on the two plans in the fixture lock: the orbiting plan put one
move on 18 of 23 shots (0.78); the varied plan's top move sat on 5 of 23
(0.22).  The ten plans written after the varied one, with the rule in prose
only, ran a top share of 0.21-0.52 -- seven of ten over a quarter."""
from types import SimpleNamespace

from studio import plan_gates as pg

MOVES = ["pushes in on the lamp", "pulls back from the door", "pans from the lamp across to the window",
         "tilts up from the boots to the face", "tracks sideways to the left past the fence",
         "tracks beside the walker as he strides along the road", "rises above the roof, looking down",
         "holds a locked-off frame", "descends from the sky to the walker"]


def plan(heads: list[str]):
    return SimpleNamespace(shots=[SimpleNamespace(index=i, motion=h + "; his hand lifts; his head turns", camera="")
                                  for i, h in enumerate(heads)])


def interleave(top: str, others: list[str], n_top: int, n: int) -> list[str]:
    """`n_top` copies of `top`, never adjacent, among `n` shots."""
    out, k = [], 0
    for i in range(n):
        if i % 2 == 0 and n_top:
            out.append(top); n_top -= 1
        else:
            out.append(others[k % len(others)]); k += 1
    return out


def test_seven_of_twenty_four_is_over_a_quarter():
    heads = interleave(MOVES[0], MOVES[1:], 7, 24)
    got = [f for f in pg.moves_faults(plan(heads)) if "share" in f]
    assert got == ["G-MOVES plan: 'push_slow' share of the 24 shots, measured 0.29 against 0.25"]


def test_six_of_twenty_four_is_a_quarter_and_passes():
    heads = interleave(MOVES[0], MOVES[1:], 6, 24)
    assert not [f for f in pg.moves_faults(plan(heads)) if "share" in f]
