"""Tests for step 02 crew mechanics — assemble, grounding, improve targeting. No LLM."""

from __future__ import annotations

import pytest

from agents import (casting_director, dialogue_editor, scene_breakdown,
                    script_supervisor, story_analyst)
from scripts.analysis import step_02_extract as s02


def _chapter():
    return {"n": 3, "part": 1, "title": "CHAPTER III.", "paragraphs": [
        {"n": 1, "text": "Holmes rose and lit his pipe by the window."},
        {"n": 2, "text": "That evening we drove to Lauriston Gardens."},
        {"n": 3, "text": "The room was empty save for a single word: RACHE."},
    ]}


def _call_sheet():
    return scene_breakdown.CallSheet(chapter=3, pov=scene_breakdown.Pov(
        narrator="Watson, first person", tense="past"), scenes=[
        scene_breakdown.Scene(n=1, para_start=1, para_end=1,
                              location_text="221B Baker Street", summary="Holmes at home"),
        scene_breakdown.Scene(n=2, para_start=2, para_end=3,
                              location_text="Lauriston Gardens", summary="The crime scene"),
    ])


def _reports():
    time_report = script_supervisor.TimeReport(chapter=3, scenes=[
        script_supervisor.SceneTime(n=2, time_evidence=[
            script_supervisor.TimeEvidence(type="time_of_day", text="That evening", para=2)],
            state_changes=[])])
    cast = casting_director.CastReport(chapter=3, scenes=[
        casting_director.SceneCast(n=1, characters=[casting_director.CastMember(
            name_text="Holmes", presence="present", role="agent", para_first=1)])])
    events = story_analyst.EventReport(chapter=3, scenes=[
        story_analyst.SceneEvents(n=2, events=[story_analyst.Event(
            type="movement", summary="They drive to Lauriston Gardens",
            participants=["Holmes", "Watson"], paras=[2],
            quote="we drove to Lauriston Gardens")])])
    dialogue = dialogue_editor.DialogueReport(chapter=3, scenes=[])
    return time_report, cast, events, dialogue


def test_assemble_merges_by_scene_number():
    extraction = s02.assemble(_call_sheet(), *_reports())
    assert extraction["chapter"] == 3
    assert len(extraction["scenes"]) == 2
    scene2 = extraction["scenes"][1]
    assert scene2["time_evidence"][0]["text"] == "That evening"
    assert scene2["events"][0]["quote"] == "we drove to Lauriston Gardens"
    assert extraction["scenes"][0]["characters"][0]["name_text"] == "Holmes"
    assert extraction["scenes"][0]["time_evidence"] == []  # missing scene -> empty, no crash


def test_check_extraction_passes_grounded():
    extraction = s02.assemble(_call_sheet(), *_reports())
    assert s02.check_extraction(extraction, _chapter()) == []


def test_check_extraction_flags_fabricated_quote():
    extraction = s02.assemble(_call_sheet(), *_reports())
    extraction["scenes"][1]["events"][0]["quote"] = "a quote that is not in the text"
    violations = s02.check_extraction(extraction, _chapter())
    assert len(violations) == 1
    assert violations[0]["dimension"] == "events"
    assert violations[0]["scene"] == 2


def test_check_extraction_raises_on_bad_para_range():
    extraction = s02.assemble(_call_sheet(), *_reports())
    extraction["scenes"][0]["para_end"] = 99
    with pytest.raises(ValueError, match="paragraph range"):
        s02.check_extraction(extraction, _chapter())


def test_audit_sample_first_middle_last():
    chapters = [{"n": i} for i in range(1, 15)]
    sample = s02._audit_sample(chapters)
    assert [c["n"] for c in sample] == [1, 8, 14]


def test_rerun_dimension_replaces_only_that_dimension(monkeypatch):
    extraction = s02.assemble(_call_sheet(), *_reports())
    fresh = script_supervisor.TimeReport(chapter=3, scenes=[
        script_supervisor.SceneTime(n=2, time_evidence=[
            script_supervisor.TimeEvidence(type="relative", text="Two days later", para=2)],
            state_changes=[])])
    monkeypatch.setattr(script_supervisor, "analyze",
                        lambda chapter, call_sheet, usage=None: fresh)
    result = s02._rerun_dimension(_chapter(), extraction, "time")
    assert result["scenes"][1]["time_evidence"][0]["text"] == "Two days later"  # replaced
    assert result["scenes"][1]["events"][0]["summary"].startswith("They drive")  # untouched


# --- completeness: specialists must answer for EVERY scene (defect found 2026-08-23) ---


def test_missing_specialist_scenes_are_detected():
    call_sheet = _call_sheet()                      # 2 scenes
    time_report, cast, events, dialogue = _reports()
    cast.scenes = []                                # specialist answered for none
    extraction = s02.assemble(call_sheet, time_report, cast, events, dialogue)
    gaps = s02.find_coverage_gaps(extraction)
    assert ("characters", 1) in gaps and ("characters", 2) in gaps


def test_no_gaps_when_specialists_cover_every_scene():
    call_sheet = _call_sheet()
    time_report, cast, events, dialogue = _reports()
    for n in (1, 2):
        if not any(s.n == n for s in cast.scenes):
            cast.scenes.append(casting_director.SceneCast(n=n, characters=[
                casting_director.CastMember(name_text="X", presence="present",
                                            role="agent", para_first=1)]))
    extraction = s02.assemble(call_sheet, time_report, cast, events, dialogue)
    assert not [g for g in s02.find_coverage_gaps(extraction) if g[0] == "characters"]
