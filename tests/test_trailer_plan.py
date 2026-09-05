"""The dynamic arc is a property of the MOVEMENT, not of the list index.

Run 10 stamped `arc` from the position of a beat in a score-sorted list, so
B00-B05 were "quiet" because they scored highest and the gate that refuses a
trailer which "never reaches a climax" passed by construction.  An arc that
cannot fail is not a gate.
"""
from __future__ import annotations

from studio.trailer_plan import arc_for, arc_of


class TestArcOfMovement:
    def test_each_movement_has_its_own_register(self):
        assert arc_of("M1") == "quiet"
        assert arc_of("M2") == "build"
        assert arc_of("M3") == "hit"

    def test_the_last_beat_is_the_aftermath(self):
        """Something must come after the climax or the hard-out has nothing
        to land against."""
        assert arc_of("M3", last=True) == "aftermath"
        assert arc_of("M1", last=True) == "aftermath"

    def test_three_movements_always_reach_a_climax(self):
        assert {arc_of(m) for m in ("M1", "M2", "M3")} == {"quiet", "build", "hit"}

    def test_the_position_rule_is_still_there_for_callers_without_a_movement(self):
        assert arc_for(0.0) == "quiet" and arc_for(0.99) == "aftermath"
