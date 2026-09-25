"""Two stills back to back read as a slideshow: a still is refused next to
another still in cut order, and the episode holds at most two.  A third
faulted narration take is kept best and flagged high instead."""
from __future__ import annotations

from studio import take_ladder


def test_a_neighbour_of_a_still_is_refused_and_a_far_take_is_not():
    order, stills = [1, 2, 3, 4, 5], {2: {}}
    assert not take_ladder.can_still(1, stills, order)
    assert not take_ladder.can_still(3, stills, order)
    assert take_ladder.can_still(4, stills, order)
    assert take_ladder.can_still(5, stills, order)


def test_neighbours_follow_cut_order_not_arithmetic():
    """Takes are named by their first shot, so the numbering has holes."""
    order = [1, 4, 9]
    assert take_ladder.neighbours(4, order) == {1, 9}
    assert take_ladder.neighbours(1, order) == {4}
    assert not take_ladder.can_still(9, {4: {}}, order)


def test_the_cap_is_two_stills_per_episode():
    order = [1, 2, 3, 4, 5, 6, 7]
    assert take_ladder.can_still(7, {1: {}}, order)
    assert not take_ladder.can_still(7, {1: {}, 4: {}}, order)
    assert not take_ladder.can_still(7, {1: {}, 4: {}}, order, cap=2)
    assert take_ladder.can_still(7, {1: {}, 4: {}}, order, cap=3)
