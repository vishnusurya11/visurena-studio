"""WHICH END of the route the landmark stands at.

The ladder was written for a corridor, where the landmark is the door you are
walking TOWARD: the farther along the route a panel stands, the larger the
landmark.  Two of this book's setups stand the other way round -- the bench's
Bunsen flame and the gateway's stone arch are at the route's START, and the
people walk AWAY from them -- so the same ladder told a wide shot taken from
the laboratory door that a one-inch flame twenty feet off filled the frame,
and the drawer drew the burner (cell Q19_1).

A landmark also has a size of its own.  A door reaches the top of the ladder at
closest approach; a flame never leaves the bottom of it.  `landmark_size` is the
biggest that THIS landmark ever stands in THIS setup, and the ladder stops
there.
"""
import pytest

from studio import episode_seq_board as sq
from studio.episode_spec import Setup


def seg(shot, sub, size, path, frame="x"):
    return {"shot": shot, "sub": sub, "size": size, "path": path, "frame": frame,
            "motion": "Static shot.", "faces": []}


BENCH = Setup(described="Holmes's own working table under the tall arched window.",
              landmark="the Bunsen lamp's blue flame on the bench",
              landmark_at="start", landmark_size="is the height of a finger",
              route="from the near end of Holmes's bench, along it under the window, to its far "
                    "end and the way back toward the door")
GATEWAY = Setup(described="The street front of the hospital.",
                landmark="the stone arch of the gateway",
                landmark_at="start", landmark_size="is half the height of the frame",
                route="from the kerb under the gateway arch and its steps, along the pavement "
                      "past the iron railings, to the corner where a cab waits")
CORRIDOR = Setup(described="A long stone corridor.", landmark="the low arched passage",
                 route="from the corridor's near end to the low arched passage at its far end")


def test_the_bench_flame_stands_smaller_the_farther_the_camera_backs_toward_the_door():
    at_the_bench, at_the_door = seg(17, 0, "medium", 0.2), seg(19, 1, "medium", 0.9)
    assert sq.ladder_clause(at_the_bench, BENCH).strip() == (
        "The Bunsen lamp's blue flame on the bench is the height of a finger.")
    assert sq.ladder_clause(at_the_door, BENCH).strip() == (
        "The Bunsen lamp's blue flame on the bench is the height of a thumbnail.")


def test_the_gateway_arch_stands_smaller_as_the_two_men_walk_off_to_the_corner():
    at_the_kerb, halfway = seg(7, 0, "wide", 0.0), seg(21, 0, "medium", 0.5)
    assert sq.ladder_clause(at_the_kerb, GATEWAY).strip() == (
        "The stone arch of the gateway is half the height of the frame.")
    assert sq.ladder_clause(halfway, GATEWAY).strip() == (
        "The stone arch of the gateway is the height of a hand.")


def test_the_order_block_says_smaller_when_the_landmark_is_at_the_route_s_start():
    text = sq.prompt([seg(7, 0, "wide", 0.0), seg(21, 0, "medium", 0.5)], GATEWAY, {},
                     previous=False, first=True, geography=True)
    assert "so the stone arch of the gateway is smaller in each of them than in the one before" in text
    assert "larger in each of them" not in text


def test_the_strict_retry_asks_for_the_same_direction_as_the_sheet():
    assert "is smaller in every route panel" in sq.strict_prefix([], [2], GATEWAY)
    assert "is larger in every route panel" in sq.strict_prefix([], [2], CORRIDOR)


def test_a_landmark_at_the_far_end_still_grows_along_the_route():
    near_end, far_end = seg(9, 0, "medium", 0.1), seg(11, 0, "full", 0.55)
    assert sq.ladder_clause(near_end, CORRIDOR).strip() == (
        "The low arched passage is the height of a thumbnail.")
    assert sq.ladder_clause(far_end, CORRIDOR).strip() == (
        "The low arched passage is the height of a hand.")
    text = sq.prompt([near_end, far_end], CORRIDOR, {}, previous=False, first=True, geography=True)
    assert "so the low arched passage is larger in each of them than in the one before" in text


def test_the_ladder_stops_at_the_size_the_landmark_reaches():
    assert sq.door_size(0.95) == "fills the frame"
    assert sq.door_size(0.95, largest="is the height of a finger") == "is the height of a finger"


def test_a_size_word_the_ladder_cannot_say_is_refused_loudly():
    with pytest.raises(ValueError, match="the height of a house"):
        sq.door_size(0.5, largest="is the height of a house")


def test_a_setup_that_names_no_route_puts_no_panel_on_one():
    bench_panel = seg(17, 0, "medium", 0.2)
    assert sq.on_route(bench_panel) is True
    assert sq.on_route(bench_panel, BENCH) is True
    assert sq.on_route(bench_panel, Setup(described="One table.", landmark="the flame")) is False
