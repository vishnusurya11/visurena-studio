"""G-MOVES: a plan needs at least eight distinct catalog moves.

The owner's oldest taste refusal -- "almost every other shot is a circle" --
was a prose rule in the camera catalog and nothing measured it.  The move id
is read from the motion head's camera clause, and from the `camera` line's
angle when the camera does not travel."""
from types import SimpleNamespace

from studio import plan_gates as pg

HEADS = ["pushes in on the lamp across the whole shot", "pulls back from the door across the whole shot",
         "pans from the lamp across to the window", "tilts up from the boots to the face",
         "tracks sideways to the left past the fence", "tracks beside the walker as he strides along the road",
         "rises above the roof, looking down over the yard", "holds a locked-off frame"]


def shots(heads: list[str], cameras: list[str] | None = None):
    cameras = cameras or [""] * len(heads)
    return [SimpleNamespace(index=i, motion=h + "; his hand lifts; his head turns", camera=c)
            for i, (h, c) in enumerate(zip(heads, cameras))]


def test_every_catalog_verb_has_its_id():
    assert pg.move_ids(shots(HEADS)) == ["push_slow", "pull_reveal", "pan_to", "tilt_up", "track_lateral",
                                         "follow", "crane_up", "locked"]


def test_an_angle_line_names_the_shot_when_the_camera_stands_still():
    still = shots(["holds a locked-off frame", "tilts down from the rim to the floor", "pushes in on the face"],
                  ["at knee height looking up at him, a low angle", "high on the rim looking down, a high angle",
                   "on the floor looking up at his face, a low angle"])
    assert pg.move_ids(still) == ["low_angle", "high_angle", "push_slow"]


def test_over_the_shoulder_is_its_own_move():
    assert pg.move_ids(shots(["holds a locked-off frame over the walker's shoulder toward the gate"])) == ["over_shoulder"]


def test_seven_moves_over_sixteen_shots_is_a_refusal():
    heads = (HEADS[:7] * 3)[:16]
    got = [f for f in pg.moves_faults(SimpleNamespace(shots=shots(heads))) if "distinct" in f]
    assert len(got) == 1
    assert got[0].startswith("G-MOVES plan: distinct catalog moves over 16 shots, measured 7 against 8")


def test_eight_moves_is_enough():
    heads = (HEADS * 3)[:16]
    assert not [f for f in pg.moves_faults(SimpleNamespace(shots=shots(heads))) if "distinct" in f]
