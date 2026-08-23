"""How precisely does the book state a time — and what may we conclude from it?

Audit 2026-08-23: every scene claimed `clock_confidence: "stated"`, including scenes
whose only signal was the DAY/NIGHT binary mapped to a placeholder hour of 12 or 22.
Downstream, the alibi query then computed travel time from `t` — the TELLING-ORDER axis
— as though it were a calendar, and reported 17 "travel-infeasible" contradictions of
the form "0.3 mi in 0.0 h", i.e. every pair of adjacent London scenes.
"""

from __future__ import annotations

from scripts.analysis import step_04_timeline as s04
from studio import storytime


# --- storytime: reading vs part ---------------------------------------------------

def test_a_clock_reading_is_a_reading():
    assert storytime.time_precision("about ten o'clock") == "reading"


def test_noon_and_midnight_are_readings():
    assert storytime.time_precision("at noon exactly") == "reading"
    assert storytime.time_precision("towards midnight") == "reading"


def test_a_part_of_the_day_is_only_a_part():
    assert storytime.time_precision("that evening") == "part"
    assert storytime.time_precision("in the morning") == "part"


def test_no_time_signal_at_all():
    assert storytime.time_precision("he opened the door") is None


# --- step 04: the binary is a default, not evidence -------------------------------

def _scene(**kw):
    base = {"chapter": 1, "scene": 1, "track": "main", "day": 1, "characters": [],
            "time_evidence": [], "time_of_day": "DAY", "location_id": "a",
            "summary": "x"}
    return {**base, **kw}


def test_day_night_alone_is_approx_never_stated():
    """DAY -> hour 12 is a placeholder. Calling it 'stated' launders a guess as
    evidence, which is the one thing this pipeline may never do."""
    scenes = s04.assign_time_of_day([_scene()])
    assert scenes[0]["clock_precision"] == "binary"
    assert scenes[0]["clock_confidence"] == "approx"


def test_a_real_clock_reading_is_stated():
    scenes = s04.assign_time_of_day(
        [_scene(time_evidence=[{"type": "time_of_day", "text": "it was six o'clock"}])])
    assert scenes[0]["clock_precision"] == "reading"
    assert scenes[0]["clock_confidence"] == "stated"
    assert scenes[0]["hour"] == 18


def test_a_part_of_day_is_stated_but_not_a_reading():
    scenes = s04.assign_time_of_day(
        [_scene(time_evidence=[{"type": "time_of_day", "text": "that evening"}])])
    assert scenes[0]["clock_precision"] == "part"
    assert scenes[0]["clock_confidence"] == "stated"


# --- the alibi query only answers when the clock is known -------------------------

LOCS = {"bart": {"lat": 51.5175, "lon": -0.1000},
        "criterion": {"lat": 51.5101, "lon": -0.1340}}


def _worldline(prec_a, hour_a, prec_b, hour_b, day_b=1):
    return {"watson": [
        {"kind": "observed", "track": "main", "t_start": 0.0, "t_end": 0.1,
         "location_id": "criterion", "day": 1, "hour": hour_a, "chapter": 1, "scene": 2,
         "clock_precision": prec_a},
        {"kind": "observed", "track": "main", "t_start": 0.1, "t_end": 0.2,
         "location_id": "bart", "day": day_b, "hour": hour_b, "chapter": 1, "scene": 3,
         "clock_precision": prec_b}]}


def test_two_vague_scenes_produce_no_travel_contradiction():
    """The book says 'morning' twice. How long the walk took is simply unknown, and
    unknown is not a contradiction."""
    wl = _worldline("part", 9, "part", 9)
    assert s04.find_contradictions(wl, LOCS) == []


def test_the_binary_default_produces_no_travel_contradiction():
    wl = _worldline("binary", 12, "binary", 12)
    assert s04.find_contradictions(wl, LOCS) == []


def test_two_clock_readings_too_close_together_do_contradict():
    """Both ends stated to the hour and the same hour — 1.5 miles in zero minutes."""
    wl = _worldline("reading", 9, "reading", 9)
    problems = s04.find_contradictions(wl, LOCS)
    assert [p["type"] for p in problems] == ["travel-infeasible"]


def test_two_clock_readings_far_enough_apart_are_fine():
    wl = _worldline("reading", 9, "reading", 11)
    assert s04.find_contradictions(wl, LOCS) == []


def test_a_reading_on_the_next_day_is_fine():
    wl = _worldline("reading", 23, "reading", 1, day_b=2)
    assert s04.find_contradictions(wl, LOCS) == []
