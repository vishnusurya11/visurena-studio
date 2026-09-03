"""Ordering shots so the cut is not the screenplay played three times."""
from __future__ import annotations

import pytest

from studio.trailer_order import allocate, interleave, is_cyclic




class TestItDeliversWhatItWasAsked:
    """Capacity was capped at 4 shots for three setups and 2 for the rest.

    Nine setups therefore topped out at 24 shots.  The cut grid asked for 31,
    `interleave` returned 24, and `shots_for` zipped the two together and
    silently dropped the last seven cuts -- 18.6 seconds of picture -- which
    the assembler then filled with a 25-second static title card.  Nothing
    reported an error; the trailer just ended early.
    """

    def test_it_returns_exactly_the_count_asked_for(self):
        setups = [f"B{i:02d}" for i in range(9)]
        for count in (9, 24, 31, 45, 60):
            assert len(interleave(setups, count)) == count, count

    def test_allocation_sums_to_the_count(self):
        setups = [f"B{i:02d}" for i in range(9)]
        assert sum(allocate(setups, 31).values()) == 31

    def test_every_setup_is_used_at_least_once(self):
        setups = [f"B{i:02d}" for i in range(9)]
        assert set(interleave(setups, 31)) == set(setups)

    def test_reuse_stays_uneven_when_capacity_grows(self):
        """Equal shares read as rationing; the fix must not flatten it."""
        setups = [f"B{i:02d}" for i in range(9)]
        counts = sorted(allocate(setups, 31).values())
        assert counts[-1] > counts[0]

    def test_no_setup_follows_itself(self):
        setups = [f"B{i:02d}" for i in range(9)]
        order = interleave(setups, 31)
        assert all(a != b for a, b in zip(order, order[1:]))

    def test_the_order_is_still_not_a_loop(self):
        setups = [f"B{i:02d}" for i in range(9)]
        assert not is_cyclic(interleave(setups, 31))

    def test_a_single_setup_cannot_avoid_following_itself(self):
        """One setup and ten shots is a legitimate impossibility; say so."""
        with pytest.raises(ValueError, match="one setup"):
            interleave(["B00"], 10)
