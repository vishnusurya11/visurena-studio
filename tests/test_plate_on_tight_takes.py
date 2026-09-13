"""The location plate is staged only where a cell can place it.

MEASURED on episode 2 (audit of all 19 takes, 88 tight frame samples against 64
wider ones): 13 of the 14 foreign frames in the episode are the take's OWN
attached plate, matched at 0.988-0.998 -- not an invented wide.  T03 opens on
Holmes's face and by 1.5 s the frame IS `plate_sofa.png`, chairs and violin and
all.  Every one came from a segment whose cell is a CLOSE or an INSERT with no
wider cell shown earlier in the take (Fisher p = 0.0072); the 18 segments with a
medium-or-wider cell produced zero, as did all 64 wider frame samples
(p = 0.00035).

The mechanism: a take with no wide cell has nothing to anchor the room to, and
the plate is then the only whole picture in its reference list.  So a take that
never shows a medium-or-wider cell does not get one.
"""
from studio.episode_seq_board import WIDE_ENOUGH, places_the_plate


def test_a_take_with_a_wide_cell_gets_the_plate():
    assert places_the_plate(["wide", "close"]) is True


def test_a_take_with_a_medium_cell_gets_the_plate():
    assert places_the_plate(["close", "medium"]) is True


def test_a_take_of_only_closes_and_inserts_does_not():
    """T03, T24 and the rest of the plate-dissolve set."""
    assert places_the_plate(["close", "insert"]) is False


def test_a_single_close_take_does_not():
    assert places_the_plate(["close"]) is False


def test_a_single_insert_take_does_not():
    assert places_the_plate(["insert"]) is False


def test_medium_close_is_not_wide_enough_to_place_a_room():
    """A medium_close is a head and shoulders; it shows no room to match."""
    assert places_the_plate(["medium_close", "close"]) is False


def test_the_ladder_is_the_one_the_route_gate_already_uses():
    assert WIDE_ENOUGH == {"medium", "full", "wide"}


def test_an_empty_take_is_not_a_crash():
    assert places_the_plate([]) is False
