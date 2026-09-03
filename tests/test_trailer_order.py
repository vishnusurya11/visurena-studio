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


SHIPPED = ("00 01 00 02 00 01 02 03 04 05 06 07 08 00 01 02 03 04 05 06 07 08 "
           "00 01 02 03 04 05 06 07 08").split()
"""The order that shipped.  B00 plays at 0.00s, 6.17s and 12.58s, and the last
eighteen shots are the beat sequence played straight through twice."""


class TestTheGateThatMissedIt:
    def test_is_cyclic_did_not_catch_the_shipped_order(self):
        """Kept as evidence.  The ragged opening defeats a prefix comparison:
        `unique` is 00 01 02 03..08 but order[:9] is 00 01 00 02 00 01 02 03 04,
        so the first equality fails and the function returns False without ever
        looking at the two verbatim runs that follow."""
        assert is_cyclic(SHIPPED) is False

    def test_the_shortest_gap_between_reuses_is_measured(self):
        from studio.trailer_order import shortest_return
        # B00 at index 0 and index 2: exactly ONE other shot between them.
        assert shortest_return(SHIPPED) == 1

    def test_the_longest_verbatim_repeat_is_measured(self):
        """00..08 appears at index 4 and again at 13.  Nine shots, twice."""
        from studio.trailer_order import longest_repeat
        assert longest_repeat(SHIPPED) >= 9

    def test_the_shipped_order_is_refused(self):
        from studio.trailer_order import refuse_repetitive
        with pytest.raises(ValueError):
            refuse_repetitive(SHIPPED)

    def test_a_returning_image_needs_room_before_it_returns(self):
        from studio.trailer_order import refuse_repetitive
        with pytest.raises(ValueError, match="returns after"):
            refuse_repetitive(["A", "B", "A", "C", "D", "E", "F", "G"])

    def test_an_order_with_no_repeats_at_all_passes(self):
        from studio.trailer_order import refuse_repetitive
        refuse_repetitive([f"B{i:02d}" for i in range(31)])

    def test_a_well_spread_order_passes(self):
        """Note what the naive fixture `i % 12` would have been: B00..B11 twice
        end to end, which is the very defect under test.  A passing example has
        to permute each pass."""
        from studio.trailer_order import refuse_repetitive
        order = ([f"B{i:02d}" for i in range(12)]
                 + [f"B{i:02d}" for i in [6, 7, 8, 9, 10, 11, 0, 1, 2, 3, 4, 5]]
                 + [f"B{i:02d}" for i in [0, 3, 6, 9, 1, 4, 7]])
        refuse_repetitive(order, min_gap=3, max_repeat=6)
