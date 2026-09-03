"""Choosing a size for every shot, not just listing which are legible.

`legible_sizes` existed, was tested, and was imported by build_plan without
ever being called.  Every shipped shot carried no size at all and every one of
the twenty-three beats carried the same camera sentence.
"""
from __future__ import annotations

import pytest

from studio.shot_grammar import (BOUND_FLOOR, LADDER, MIN_SECONDS, choose_sizes,
                                 ladder_distance)


def positions(n: int) -> list[float]:
    return [i / max(n - 1, 1) for i in range(n)]


class TestChooseSizes:
    def test_every_size_is_legible_for_its_own_duration(self):
        lengths = [0.6, 2.9, 1.2, 3.4, 0.8, 2.1, 1.7, 2.6]
        sizes = choose_sizes(lengths, [False] * 8, positions(8))
        for size, seconds in zip(sizes, lengths):
            assert MIN_SECONDS[size] <= seconds

    def test_it_returns_one_size_per_shot(self):
        assert len(choose_sizes([1.0] * 5, [False] * 5, positions(5))) == 5

    def test_neighbours_never_repeat_a_size(self):
        """Two shots at the same size cut together read as a jump, not a cut."""
        lengths = [2.0, 2.1, 2.0, 2.2, 2.0, 2.1, 2.0]
        sizes = choose_sizes(lengths, [False] * 7, positions(7))
        assert all(a != b for a, b in zip(sizes, sizes[1:])), sizes

    def test_neighbours_move_at_least_two_rungs_when_the_room_exists(self):
        lengths = [3.5] * 6
        sizes = choose_sizes(lengths, [False] * 6, positions(6))
        assert all(ladder_distance(a, b) >= 2 for a, b in zip(sizes, sizes[1:])), sizes

    def test_a_shot_carrying_a_character_is_never_wider_than_the_floor(self):
        """A reference sheet spent on twenty pixels of face is a reference
        nobody can see, and the binding gate passes it anyway."""
        lengths = [3.5] * 6
        sizes = choose_sizes(lengths, [True] * 6, positions(6))
        floor = LADDER.index(BOUND_FLOOR)
        assert all(LADDER.index(s) <= floor for s in sizes), sizes

    def test_the_trough_tightens(self):
        """MEASURED across 50 released trailers: shots reach their shortest at
        85-90%.  A wide there is a flash of nothing."""
        lengths = [3.5] * 12
        sizes = choose_sizes(lengths, [False] * 12, positions(12))
        late = LADDER.index(sizes[10])
        assert late <= LADDER.index("medium"), sizes

    def test_a_short_shot_cannot_be_given_a_wide(self):
        sizes = choose_sizes([0.6], [False], [0.0])
        assert MIN_SECONDS[sizes[0]] <= 0.6

    def test_it_refuses_a_shot_too_short_for_any_size(self):
        with pytest.raises(ValueError, match="0.2"):
            choose_sizes([0.2], [False], [0.0])
