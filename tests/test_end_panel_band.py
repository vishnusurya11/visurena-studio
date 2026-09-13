"""A panel and its own END panel must be ALIKE, within a band.

`ALIKE = 0.70` is a CEILING with no floor, which is right for two different
panels and exactly backwards for a panel and its own END.  An END is the same
picture after ONE SIMPLE CAMERA MOVE, so it should be very similar; the gate
instead rewarded making it a different picture, and punished obeying the rule.

MEASURED on episode 2's 54 cells: 9 of 12 start/END pairs are re-stages, median
similarity 0.307 and minimum -0.019 -- two pictures of one segment with no
statistical relationship.  The three pairs that DO obey the movement rule
(0.553, 0.569, 0.602) are among the five most-alike pairs in the whole episode
and were the nearest to being refused as copies.

This is the drift fault seen from the drawing side: `take_verdict.drift_gate`
measures whether the render REACHES its END cell, and a re-staged END cannot be
reached by a camera move.  Seven takes failed drift; nine ENDs are re-stages.
"""
import pytest

from studio.episode_seq_board import ALIKE, END_CEILING, END_FLOOR, end_pair_verdict


def test_the_band_sits_below_the_twin_ceiling_at_the_top():
    """An END may be MORE alike than two different panels are allowed to be --
    that is the point of it -- but not a pixel copy."""
    assert END_FLOOR < END_CEILING
    assert END_CEILING > ALIKE


def test_a_camera_move_apart_passes():
    assert end_pair_verdict(0.553) == "ok"
    assert end_pair_verdict(0.602) == "ok"
    assert end_pair_verdict(0.70) == "ok"


def test_a_restaged_end_is_refused():
    """The 9 that would have been caught: a different picture, not a move."""
    for score in (-0.019, 0.121, 0.307, 0.44):
        assert end_pair_verdict(score) == "restaged"


def test_a_copied_end_is_still_refused():
    """The original fault: told 'identical to panel 1', the drawer drew panel 1
    again -- 0.951, 0.890 and 0.821 on disk."""
    for score in (0.821, 0.890, 0.951):
        assert end_pair_verdict(score) == "copy"


def test_the_boundaries_are_inclusive_at_the_floor_and_the_ceiling():
    assert end_pair_verdict(END_FLOOR) == "ok"
    assert end_pair_verdict(END_CEILING) == "ok"
    assert end_pair_verdict(END_FLOOR - 0.001) == "restaged"
    assert end_pair_verdict(END_CEILING + 0.001) == "copy"


@pytest.mark.parametrize("score", [0.46, 0.5, 0.6, 0.7, 0.8])
def test_the_band_accepts_the_whole_range_a_camera_move_produces(score):
    assert end_pair_verdict(score) == "ok"
