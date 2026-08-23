"""Tests for agents.journey_tracer and its wiring into the timeline. LLM always faked.

A summary sweep ("India, Afghanistan, Peshawar, England, and London") is not one place
and cannot be made into one. These tests pin the behaviour that keeps it a sequence.
"""

from __future__ import annotations

from agents import journey_tracer as jt
from scripts.analysis import step_04_timeline as s04

LOCATIONS = {
    "maiwand": {"name": "Maiwand", "aliases": ["the fatal battle of Maiwand"],
                "region": "afghanistan"},
    "peshawar": {"name": "Peshawar", "aliases": ["the base hospital at Peshawar"],
                 "region": "india"},
    "london": {"name": "London", "aliases": ["the metropolis"], "region": "london"},
    "baker": {"name": "221B Baker Street", "aliases": [], "region": "london"},
}


def _sweep():
    return {"chapter": 1, "scene": 1, "type": "nonscene", "track": "main", "day": 1,
            "t": 0.0, "location_id": "london", "location_confidence": "inferred",
            "location_text": "India, Afghanistan, Peshawar, England, and London",
            "summary": "Watson summarizes his service, wounding and return.",
            "characters": ["john_watson"], "time_evidence": [], "time_of_day": "DAY"}


def _journey():
    return jt.Journey(
        is_journey=True, primary_location_id="maiwand", reasoning="two years, six places",
        legs=[jt.Leg(order=1, location_id="maiwand", when="1880, the battle",
                     event="Watson is shot in the shoulder", time_of_day="DAY"),
              jt.Leg(order=2, location_id="peshawar", when="the months after",
                     event="he convalesces, then takes enteric fever", time_of_day="DAY"),
              jt.Leg(order=3, location_id="london", when="on returning to England",
                     event="he gravitates to London", time_of_day="DAY")])


# --- candidate detection: which spans are even worth asking about ------------------

def test_a_span_naming_several_canonical_places_is_a_candidate():
    assert s04.journey_candidates([_sweep()], LOCATIONS) == [0]


def test_one_room_inside_one_building_is_not_a_candidate():
    """'the sitting-room, 221B Baker Street' names a container, not a journey."""
    scene = {**_sweep(), "type": "scene",
             "location_text": "the sitting-room, 221B Baker Street"}
    assert s04.journey_candidates([scene], LOCATIONS) == []


def test_two_places_in_the_same_region_are_not_a_journey():
    scene = {**_sweep(), "location_text": "221B Baker Street and London"}
    assert s04.journey_candidates([scene], LOCATIONS) == []


# --- tracing -----------------------------------------------------------------------

def test_legs_are_recorded_in_order_with_the_primary_place(monkeypatch):
    monkeypatch.setattr(jt, "trace", lambda *a, **k: _journey())
    scenes = [_sweep()]
    assert s04.trace_journeys(scenes, LOCATIONS) == 1
    assert [leg["location_id"] for leg in scenes[0]["legs"]] == \
        ["maiwand", "peshawar", "london"]
    assert scenes[0]["location_id"] == "maiwand"        # where the wound happens
    assert scenes[0]["location_confidence"] == "traversal"


def test_a_leg_with_an_invented_id_is_dropped_not_trusted(monkeypatch):
    bad = _journey()
    bad.legs[1].location_id = "atlantis"
    monkeypatch.setattr(jt, "trace", lambda *a, **k: bad)
    scenes = [_sweep()]
    s04.trace_journeys(scenes, LOCATIONS)
    assert [leg["location_id"] for leg in scenes[0]["legs"]] == ["maiwand", "london"]


def test_the_agent_may_say_the_span_is_really_one_place(monkeypatch):
    verdict = _journey()
    verdict.is_journey = False
    monkeypatch.setattr(jt, "trace", lambda *a, **k: verdict)
    scenes = [_sweep()]
    assert s04.trace_journeys(scenes, LOCATIONS) == 0
    assert "legs" not in scenes[0]
    assert scenes[0]["location_id"] == "london"         # left exactly as it was


def test_a_single_leg_is_not_a_journey(monkeypatch):
    """One place is a placement, not a traversal — do not dress it up as one."""
    lone = _journey()
    lone.legs = lone.legs[:1]
    monkeypatch.setattr(jt, "trace", lambda *a, **k: lone)
    scenes = [_sweep()]
    assert s04.trace_journeys(scenes, LOCATIONS) == 0
    assert "legs" not in scenes[0]


def test_agent_failure_leaves_the_scene_alone(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("model unavailable")
    monkeypatch.setattr(jt, "trace", boom)
    scenes = [_sweep()]
    assert s04.trace_journeys(scenes, LOCATIONS) == 0
    assert scenes[0]["location_id"] == "london"


# --- the payoff: the character actually moves -------------------------------------

def test_a_traversing_character_gets_one_worldline_point_per_leg(monkeypatch):
    monkeypatch.setattr(jt, "trace", lambda *a, **k: _journey())
    scenes = [_sweep()]
    s04.trace_journeys(scenes, LOCATIONS)
    worldlines = s04.build_worldlines(scenes)
    observed = [s for s in worldlines["john_watson"] if s["kind"] == "observed"]
    assert [s["location_id"] for s in observed] == ["maiwand", "peshawar", "london"]
    assert observed[0]["t_start"] < observed[1]["t_start"] < observed[2]["t_start"]


def test_leg_points_stay_inside_their_scene_slot(monkeypatch):
    """The legs subdivide the scene's own slot — they must not run over the next
    scene and reorder the book."""
    monkeypatch.setattr(jt, "trace", lambda *a, **k: _journey())
    scenes = [_sweep(), {**_sweep(), "scene": 2, "t": 1.0, "legs": None,
                         "location_text": "the Criterion Bar", "location_id": "london"}]
    scenes[1].pop("legs")
    s04.trace_journeys(scenes[:1], LOCATIONS)
    worldlines = s04.build_worldlines(scenes)
    points = [s for s in worldlines["john_watson"] if s["kind"] == "observed"]
    assert all(p["t_start"] < 1.0 for p in points[:3])
    assert points[3]["t_start"] == 1.0


def test_consecutive_legs_are_not_a_bilocation(monkeypatch):
    """A route's legs are sequential BY CONSTRUCTION. Reading them as 'two places at
    overlapping story time' would have the tracer manufacture the very contradictions
    the timeline exists to catch."""
    monkeypatch.setattr(jt, "trace", lambda *a, **k: _journey())
    scenes = [_sweep(), {**_sweep(), "scene": 2, "t": 0.2,
                         "location_text": "the Criterion Bar", "location_id": "london"}]
    s04.trace_journeys(scenes[:1], LOCATIONS)
    worldlines = s04.build_worldlines(scenes)
    coords = {"maiwand": {"lat": 32.0, "lon": 65.0}, "peshawar": {"lat": 34.0, "lon": 71.6},
              "london": {"lat": 51.5, "lon": -0.13}, "baker": {"lat": 51.5, "lon": -0.16}}
    assert [c for c in s04.find_contradictions(worldlines, coords)
            if c["type"] == "bilocation"] == []


def test_an_observation_ends_when_the_next_one_begins():
    """The 0.12 dwell is a default, not a floor — a tight slot shortens it."""
    scenes = [{"chapter": 1, "scene": 1, "track": "main", "day": 1, "t": 0.0,
               "location_id": "a", "summary": "x", "characters": ["c"]},
              {"chapter": 1, "scene": 2, "track": "main", "day": 1, "t": 0.05,
               "location_id": "b", "summary": "y", "characters": ["c"]}]
    observed = [s for s in s04.build_worldlines(scenes)["c"] if s["kind"] == "observed"]
    assert observed[0]["t_end"] == 0.05
