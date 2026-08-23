"""Tests for agents.gap_filler and its wiring into the timeline. LLM always faked."""

from __future__ import annotations

import pytest

from agents import gap_filler
from scripts.analysis import step_04_timeline as s04


def _scenes():
    return [
        {"chapter": 6, "scene": 1, "track": "main", "day": 1, "location_id": "baker",
         "location_text": "221B", "summary": "at home", "characters": ["holmes"],
         "time_evidence": [], "time_of_day": "DAY"},
        {"chapter": 6, "scene": 2, "track": "main", "day": 1, "location_id": None,
         "location_text": "the newspapers", "summary": "Watson reads the papers",
         "characters": ["watson"], "time_evidence": [], "time_of_day": "UNKNOWN"},
        {"chapter": 6, "scene": 3, "track": "main", "day": 1, "location_id": "baker",
         "location_text": "221B", "summary": "Gregson arrives", "characters": [],
         "time_evidence": [], "time_of_day": "DAY"},
    ]


def test_gap_is_filled_and_marked_inferred(monkeypatch):
    monkeypatch.setattr(gap_filler, "place",
                        lambda *a, **k: gap_filler.Placement(
                            location_id="baker", time_of_day="DAY", confidence="high",
                            reasoning="both neighbours are at Baker Street"))
    scenes = _scenes()
    filled = s04.fill_location_gaps(scenes, {"baker": {"name": "221B", "region": "london"}})
    assert filled == 1
    assert scenes[1]["location_id"] == "baker"
    assert scenes[1]["location_confidence"] == "inferred"
    assert "Baker Street" in scenes[1]["location_reasoning"]


def test_every_scene_ends_up_placed(monkeypatch):
    """Owner rule: abstaining is not on offer — a summary sweep still gets the most
    consequential place in its span."""
    monkeypatch.setattr(gap_filler, "place",
                        lambda *a, **k: gap_filler.Placement(
                            location_id="baker", time_of_day="DAY", confidence="low",
                            reasoning="a backstory sweep; Baker Street is the anchor"))
    scenes = _scenes()
    s04.fill_location_gaps(scenes, {"baker": {"name": "221B"}})
    assert all(s["location_id"] for s in scenes)
    assert scenes[1]["location_inference_confidence"] == "low"


def test_a_scene_missing_only_its_time_is_still_filled(monkeypatch):
    monkeypatch.setattr(gap_filler, "place",
                        lambda *a, **k: gap_filler.Placement(
                            location_id="baker", time_of_day="NIGHT",
                            confidence="medium", reasoning="continues an evening scene"))
    scenes = _scenes()
    scenes[0]["time_of_day"] = "UNKNOWN"
    s04.fill_location_gaps(scenes, {"baker": {"name": "221B"}})
    assert scenes[0]["time_of_day"] == "NIGHT"
    assert scenes[0]["location_id"] == "baker"          # its stated place is kept
    assert scenes[0]["location_confidence"] == "stated"


def test_resolved_scenes_are_never_touched(monkeypatch):
    called = []
    monkeypatch.setattr(gap_filler, "place",
                        lambda *a, **k: called.append(1) or gap_filler.Placement(
                            location_id="baker", time_of_day="DAY", confidence="high",
                            reasoning="x"))
    scenes = _scenes()
    s04.fill_location_gaps(scenes, {"baker": {"name": "221B"}})
    assert len(called) == 1                       # only the one gap
    assert scenes[0]["location_confidence"] == "stated"


def test_hallucinated_location_id_is_rejected(monkeypatch):
    monkeypatch.setattr(gap_filler, "place",
                        lambda *a, **k: gap_filler.Placement(
                            location_id="atlantis", time_of_day="DAY",
                            confidence="high", reasoning="invented"))
    scenes = _scenes()
    filled = s04.fill_location_gaps(scenes, {"baker": {"name": "221B"}})
    assert filled == 0
    assert scenes[1]["location_id"] is None       # not in the canonical list -> refused


def test_agent_failure_leaves_the_gap_alone(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("model unavailable")
    monkeypatch.setattr(gap_filler, "place", boom)
    scenes = _scenes()
    assert s04.fill_location_gaps(scenes, {"baker": {"name": "221B"}}) == 0
    assert scenes[1]["location_id"] is None
