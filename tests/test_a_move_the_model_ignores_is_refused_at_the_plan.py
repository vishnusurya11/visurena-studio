"""G-STILL: a move MiniMax-H3 ignores is refused at the plan, before a render.

ep13 first pass (2026-09-27, speed plan #8): rack_focus 2/2 and tilt_down 2/2
failed (frozen whole frame, or off its panel); the three angle holds read
82-100 % static.  docs/calibration/camera_catalog.md already said "Moves H3
ignores: crane_down, rack_focus, tilt_down. Use crane_up, pull_reveal and
track_lateral instead" -- and no gate read it.  A shot the plan declares
`still` is a hold on purpose and is not refused.
"""
from types import SimpleNamespace as S

from studio import plan_gates as pg


def shot(motion, camera="level with his eyes, an 85mm lens", still=False, index=4):
    return S(index=index, motion=motion, camera=camera, still=still)


def test_rack_focus_and_tilt_down_are_refused_with_their_substitute():
    got = pg.still_faults(S(shots=[
        shot("The camera racks focus from the hedge leaves onto his face; he asks", index=13),
        shot("The camera tilts down from the hedge top onto his face; he asks", index=19)]))
    assert len(got) == 2 and "G-STILL shot 13" in got[0] and "pull_reveal" in got[0]
    assert "G-STILL shot 19" in got[1]


def test_an_angle_hold_with_no_move_is_refused():
    got = pg.still_faults(S(shots=[shot("The camera holds from low in the grass; his hand goes on shaking",
                                        camera="low angle, at knee height in the grass, looking up at him")]))
    assert len(got) == 1 and "low_angle" in got[0]


def test_an_angle_with_a_move_passes():
    assert pg.still_faults(S(shots=[shot("The camera cranes up from low in the grass; he rises",
                                         camera="low angle, looking up at him")])) == []


def test_a_declared_still_hold_passes():
    assert pg.still_faults(S(shots=[shot("The camera holds from low; he lies still",
                                         camera="low angle, looking up", still=True)])) == []


def test_the_moves_it_obeys_pass():
    motions = ["The camera pushes in toward him", "The camera pans to the gun", "The camera tilts up to the sky",
               "The camera tracks sideways along the water", "The camera orbits a quarter turn around him"]
    assert pg.still_faults(S(shots=[shot(m) for m in motions])) == []
