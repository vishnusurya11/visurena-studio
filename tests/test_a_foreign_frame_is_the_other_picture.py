r"""`FOREIGN_MIN = 0.60` was calibrated in a world where the camera never moved.

EPISODE 6 IS THE FIRST WHERE EVERY SHOT HEAD NAMES A CAMERA MOVE (26 of 26,
against episode 5's 7 of 25). Stillness went to exactly zero -- frozen-share
0.0 and frozen-at-start 0.0 over all 26 takes, against 67.2 and 25.0 points in
episode 5. And then three takes failed HARD on `foreign`, for 90 points, which
is almost exactly the stillness loss it replaced.

All three are false positives, confirmed by eye:

    T20  last frame is Gregson pushed in;   "foreign" cell is two women in
                                            another room        (own 0.603, other 0.659)
    T18  last frame is Madame Charpentier;  "foreign" cell is Holmes at a
                                            window              (own 0.179, other 0.610)
    T15  last frame is her parlour with the mother entering at the LEFT, which
         is what the motion asked for;      "foreign" cell is the two women
                                            at the table        (own 0.320, other 0.618)

THE MECHANISM IS THE CAMERA MOVE ITSELF. A take is compared against its own
STATIC start cell. While the camera held, own-similarity stayed near 0.9 and
`other > own + FOREIGN_MARGIN` could almost never fire. Once the camera pushes
in or cranes, the frame legitimately stops resembling the cell it began on --
T20 decays 0.999 -> 0.603 across 4.3 seconds, exactly as instructed -- and any
unrelated cell sitting at the instrument's noise floor (~0.585) can edge past
it. The margin test stopped being a discriminator the moment the pictures
started moving.

THE TWO POPULATIONS ARE CLEANLY SEPARATED, and not by the margin:

    REAL      the other picture is the take's own PLATE, a whole empty room,
              and the score CLIMBS toward 1.0
              ep03 T08  plate_garden_path  0.763 -> 0.965
              ep02      13 of 14 foreign frames were the plate, 0.988-0.998

    ARTIFACT  the other picture is an unrelated CELL, flat near the noise floor
              ep03 T12  Q23_0          0.721
              ep03 T22  Q06_0.before   0.629
              ep06 T15/T18/T20         0.610-0.659

So the floor moves to where the word means what it says. `LAND`'s own
calibration is the precedent: "a frame that reproduces its pinned cell scores
0.95-1.00". A foreign frame is one that IS the other picture, and 0.60 is the
floor for a MISS, not for a match.

This does not weaken the gate against the fault it was built for. Episode 2's
plate intrusions measured 0.988-0.998 and episode 3's T08 reaches 0.965; every
one still fires, with room to spare.
"""
import pytest

from studio.cut_landing import FOREIGN_MARGIN, FOREIGN_MIN


def foreign(own: float, other: float) -> bool:
    """The gate's own rule, stated once here so the test cannot drift from it."""
    return other > own + FOREIGN_MARGIN and other >= FOREIGN_MIN


# ---- the faults it exists to catch, measured -------------------------------

def test_the_plate_taking_over_a_frame_is_foreign():
    """ep03 T08 at 6.58 s: the take's own `plate_garden_path` at 0.965."""
    assert foreign(own=0.406, other=0.965)


def test_episode_twos_plate_intrusions_still_fire():
    """13 of 14 measured 0.988-0.998 -- T03 opens on a face and by 1.5 s the
    frame IS `plate_sofa.png`, chairs and violin and all."""
    for other in (0.988, 0.993, 0.998):
        assert foreign(own=0.40, other=other), other


def test_a_real_intrusion_fires_even_when_its_own_cell_still_reads_well():
    assert foreign(own=0.60, other=0.97)


# ---- the artifacts a moving camera creates ---------------------------------

def test_a_pushed_in_take_is_not_foreign():
    """ep06 T20: the last frame is plainly Gregson, and the cell that beat it
    is two women in a different room."""
    assert not foreign(own=0.603, other=0.659)


def test_a_take_that_matches_nothing_much_is_not_foreign():
    """ep06 T18, own 0.179. A frame matching nothing is off its own
    composition, which is DRIFT's business -- the module's own words."""
    assert not foreign(own=0.179, other=0.610)


def test_the_episode_three_cell_flags_are_not_foreign_either():
    assert not foreign(own=0.608, other=0.721)      # T12, Q23_0
    assert not foreign(own=0.380, other=0.629)      # T22, Q06_0.before


def test_the_whole_artifact_population_is_rejected():
    for own, other in ((0.603, 0.659), (0.320, 0.618), (0.179, 0.610),
                       (0.608, 0.721), (0.380, 0.629)):
        assert not foreign(own, other), (own, other)


def test_the_whole_real_population_is_kept():
    for own, other in ((0.406, 0.965), (0.40, 0.988), (0.40, 0.998)):
        assert foreign(own, other), (own, other)


# ---- the constant itself ----------------------------------------------------

def test_the_floor_is_a_match_not_a_miss():
    """`LAND`'s calibration: a frame that reproduces its cell scores 0.95-1.00.
    A foreign frame is one that IS the other picture."""
    assert FOREIGN_MIN >= 0.85


def test_the_floor_clears_the_instruments_noise_by_a_wide_margin():
    """`frame_match` reads ~0.585 between two unrelated pictures. The old 0.60
    sat 0.015 above that, which is why a moving camera walked straight through
    it."""
    assert FOREIGN_MIN - 0.585 > 0.25


def test_the_margin_is_unchanged():
    """Only the floor moved. The margin was never the thing that was wrong."""
    assert FOREIGN_MARGIN == 0.05
