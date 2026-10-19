"""eta.py charges only the units still owed, prints a band until per-take seconds are measured,
the 6 h hard stop as a time of day, the flagged debt in seconds and the fixes waiting (Jekyll
Kawajiri ep01: 7 stale takes were priced as 28 and the step-level will_run landed past the hard
stop).  Pure; $0."""
from __future__ import annotations

from studio import eta

FRAMES = 192
NOW, SIX_H = 1_800_000_000.0, 6 * 3600.0


def test_seven_owed_takes_cost_about_seven_takes_not_twenty_eight():
    seven = eta.owed_eta([FRAMES] * 7, [], now=NOW, work_s=0.0)
    every = eta.owed_eta([FRAMES] * 28, [], now=NOW, work_s=0.0)
    assert 3.5 < every["mid_s"] / seven["mid_s"] < 4.5


def test_a_band_not_a_point_until_per_take_seconds_are_measured():
    got = eta.owed_eta([FRAMES] * 7, [], now=NOW, work_s=0.0)
    assert got["lo_s"] < got["mid_s"] < got["hi_s"] and got["basis"] == "estimate"


def test_measured_takes_narrow_the_band_and_say_measured():
    prior = eta.take_prior(FRAMES)
    done = [(prior * r, FRAMES) for r in (0.9, 1.0, 1.1, 1.0)]
    cold = eta.owed_eta([FRAMES] * 7, [], now=NOW, work_s=0.0)
    got = eta.owed_eta([FRAMES] * 7, done, now=NOW, work_s=0.0)
    assert got["basis"] == "measured" and (got["hi_s"] - got["lo_s"]) < (cold["hi_s"] - cold["lo_s"])


def test_nothing_owed_is_zero_left():
    got = eta.owed_eta([], [], now=NOW, work_s=100.0)
    assert (got["lo_s"], got["mid_s"], got["hi_s"]) == (0.0, 0.0, 0.0) and not got["over"]


def test_the_hard_stop_is_the_six_hour_line_less_the_work_done():
    got = eta.owed_eta([FRAMES], [], now=NOW, work_s=5 * 3600.0)
    assert got["hard_stop_at"] == NOW + 3600.0


def test_a_band_that_ends_past_the_hard_stop_says_over():
    got = eta.owed_eta([FRAMES] * 28, [], now=NOW, work_s=SIX_H - 600.0)
    assert got["over"] is True


def test_the_hard_stop_line_names_the_time_and_the_hours_used():
    line = eta.hard_stop_words(NOW + 3600.0, 5 * 3600.0, lambda t: "9:40 pm")
    assert line == "hard stop 9:40 pm · 5h00 of 6h used"


def test_the_flagged_takes_ship_line_sums_their_seconds():
    rows = [{"take": "T07", "seconds_in_master": 2.5}, {"take": "T10", "seconds_in_master": 3.0}]
    assert eta.flagged_words(rows) == "2 flagged takes ship, 5.5 s total"
    assert eta.flagged_words(rows[:1]) == "1 flagged take ships, 2.5 s total"
    assert eta.flagged_words([]) == ""


def test_the_fixes_waiting_line():
    assert eta.fixes_words(0) == ""
    assert eta.fixes_words(1) == "1 fix waiting for the next pause"
    assert eta.fixes_words(4) == "4 fixes waiting for the next pause"


def test_unit_state_beats_the_step_level_guess():
    owed = eta.owed_eta([FRAMES] * 2, [], now=NOW, work_s=0.0)
    assert eta.left_for_step(9999.0, owed) == owed["mid_s"]
    assert eta.left_for_step(9999.0, None) == 9999.0
