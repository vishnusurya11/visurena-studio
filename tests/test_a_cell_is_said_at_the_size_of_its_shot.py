"""A shot that is not a wide never carries its setup's WIDE geometry.

Audit item 20, measured 2026-09-22. A setup's `geometry` lays out the whole
place for its establishing wide. Pasted into a tighter shot, the drawer obeys
the cells and draws the place:
- ep09 shot 22, a big close-up of the hussar, came back an empty garden;
- ep09 shot 12, a medium on two people at tea, came back an empty lawn;
- ep08 shot 6, an insert on a newspaper, came back the wide platform with a
  paper in one corner;
- ep07 shot 13, a medium, came back two pictures stacked in one frame.
Across ep06-ep09 the setup's wide geometry sat verbatim in 35 non-wide shots.
"""
from studio.picture_gates import scale_faults


class Shot:
    def __init__(self, index, size, at_rest):
        self.index, self.size, self.at_rest, self.setup = index, size, at_rest, "s"


class Setup:
    geometry = "The lawn fills the BOTTOM half. The wall runs across the CENTRE."


class Episode:
    def __init__(self, shots):
        self.shots, self.setups = shots, {"s": Setup()}


def test_a_wide_may_carry_the_setups_geometry():
    assert scale_faults(Episode([Shot(0, "wide", Setup.geometry)])) == []


def test_a_medium_carrying_it_is_a_fault():
    got = scale_faults(Episode([Shot(3, "medium", Setup.geometry + " Their heads are small.")]))
    assert len(got) == 1 and "shot 3" in got[0]


def test_an_insert_and_a_close_carrying_it_are_faults():
    ep = Episode([Shot(1, "insert", Setup.geometry), Shot(2, "close", Setup.geometry)])
    assert len(scale_faults(ep)) == 2


def test_a_tight_shot_with_its_own_cells_is_clean():
    assert scale_faults(Episode([Shot(4, "medium", "His head and shoulders fill the CENTRE.")])) == []


def test_a_setup_with_no_geometry_never_accuses_anyone():
    ep = Episode([Shot(5, "close", "anything")])
    ep.setups["s"].geometry = ""
    try:
        assert scale_faults(ep) == []
    finally:
        ep.setups["s"].geometry = Setup.geometry
