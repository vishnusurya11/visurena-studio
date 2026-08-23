"""A time phrase dates the moment it NAMES, not the scene that names it.

Audit 2026-08-23. Two contradictions survived every other fix, and both were the same
error — the same one that once dated the London investigation to 1878 because Watson
mentioned his degree year, now committed against hours instead of years:

  ch6 sc4  Gregson RECOUNTS three weeks of legwork, "after twelve o'clock in the day".
           The scene was stamped noon. The noon belongs to the errand he describes.
  ch11 sc11 A sentinel repeats the standing countersign, "To-morrow at midnight".
           The scene was stamped midnight. It happens at daybreak.

Both then read as a character travelling backwards through time. Mention is not
occurrence — the rule scene_breakdown already applies to places, applied to clocks.
"""

from __future__ import annotations

from scripts.analysis import step_04_timeline as s04


# --- what survives is reported as what it is --------------------------------------

LOCS = {"a": {"lat": 51.51, "lon": -0.10}, "b": {"lat": 51.52, "lon": -0.16}}


def test_time_running_backwards_is_reported_as_its_own_kind():
    """Not 'travel-infeasible' — no speed of travel fixes a negative interval."""
    wl = {"gregson": [
        {"kind": "observed", "track": "main", "t_start": 0.0, "t_end": 0.1, "day": 6,
         "hour": 12, "clock_precision": "reading", "location_id": "a",
         "chapter": 6, "scene": 4},
        {"kind": "observed", "track": "main", "t_start": 0.1, "t_end": 0.2, "day": 6,
         "hour": 6, "clock_precision": "reading", "location_id": "b",
         "chapter": 6, "scene": 6}]}
    problems = s04.find_contradictions(wl, LOCS)
    assert [p["type"] for p in problems] == ["clock-reversed"]
    assert "backwards" in problems[0]["note"]
