"""The shape of the tail: hard out, silence, hit, hold.

Run 10 faded the cue out over 3 s into digital silence and then struck the
card where the music had already died -- the card measured -46 LUFS.  A
button is a STOP, a held breath, and then a hit while there is still a cue
alive to hit with.
"""
from __future__ import annotations

import pytest

from studio.trailer_cut import (FINAL_HOLD, PRE_TITLE_SILENCE, is_uniform,
                                target_length, title_moment)


class TestTitleMoment:
    def test_the_bed_stops_on_the_last_cut(self):
        hard_out, _, _ = title_moment(80.0)
        assert hard_out == 80.0

    def test_the_hit_lands_after_a_held_silence(self):
        hard_out, hit, _ = title_moment(80.0)
        assert hit - hard_out == pytest.approx(PRE_TITLE_SILENCE)

    def test_the_card_covers_the_silence_and_the_whole_tail(self):
        _, hit, card = title_moment(80.0)
        assert card == pytest.approx(PRE_TITLE_SILENCE + FINAL_HOLD)
        assert 80.0 + card - hit >= 3.0

    def test_a_longer_hold_lengthens_the_card_not_the_silence(self):
        hard_out, hit, card = title_moment(80.0, hold=6.0)
        assert hit == title_moment(80.0)[1] and card == PRE_TITLE_SILENCE + 6.0


class TestTheHeldBreath:
    """D: pre-title silence M <= -35 for >= 1.5 s.  Momentary loudness is a
    400 ms trailing window, so the first 0.4 s of any silence still reads the
    music that preceded it -- the gap has to be longer than the rule by that
    window or the rule cannot be met."""

    def test_the_silence_outlasts_the_momentary_window_plus_the_rule(self):
        assert PRE_TITLE_SILENCE - 0.4 >= 1.5

    def test_it_stays_inside_what_reads_as_a_breath_not_a_fault(self):
        assert PRE_TITLE_SILENCE <= 2.5


class TestFinalHold:
    def test_the_hold_outlasts_every_arc_target(self):
        assert FINAL_HOLD > max(target_length(p / 100) for p in range(100))

    def test_the_card_holds_long_enough_for_the_hit_to_decay(self):
        """D: title hold >= 4 s.  Run 10 held 3.0 and ended while the hit
        was still decaying -- M -49 at 104.7 s of a 105.08 s file."""
        assert FINAL_HOLD >= 4.0


class TestUniform:
    def test_two_shots_are_not_a_pattern(self):
        assert not is_uniform([2.0, 2.0])
        assert is_uniform([2.0, 2.0, 2.0])
