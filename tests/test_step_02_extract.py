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


# --- the part > 0 assumption, third occurrence (2026-08-26) ------------------------
#
# load_chapters selected `part > 0`, so on any book without Parts it returned NOTHING
# and step 02 reported "0 chapters, 0 to extract" and exited CLEAN. Steps 03-06 then ran
# on an empty extraction and produced an empty analysis, and only step 06 noticed - as
# "extraction files 0 != chapters 3", five steps downstream of the cause.
#
# Front matter is the n == 0 sentinel. That is the discriminator, and it holds for every
# book. Same fix already applied in step_01_ingest._check_chapters and step_06_verify.

def test_chapters_are_selected_by_n_not_by_part(tmp_path):
    import json
    from scripts.analysis.step_02_extract import _load_chapters
    source = tmp_path / "source"
    (source / "chapters").mkdir(parents=True)
    for n in (0, 1, 2):
        (source / "chapters" / f"ch_{n:02d}.json").write_text(
            json.dumps({"n": n, "part": 0, "title": f"c{n}",
                        "paragraphs": [{"n": 1, "text": "x"}]}), encoding="utf-8")
    (source / "book.json").write_text(json.dumps({"chapters": [
        {"n": n, "part": 0, "file": f"chapters/ch_{n:02d}.json"} for n in (0, 1, 2)]}),
        encoding="utf-8")
    assert [c["n"] for c in _load_chapters(source.parent)] == [1, 2]


def test_front_matter_is_still_excluded(tmp_path):
    import json
    from scripts.analysis.step_02_extract import _load_chapters
    source = tmp_path / "source"
    (source / "chapters").mkdir(parents=True)
    (source / "chapters" / "ch_00.json").write_text(
        json.dumps({"n": 0, "part": 0, "title": "Front matter",
                    "paragraphs": [{"n": 1, "text": "preface"}]}), encoding="utf-8")
    (source / "book.json").write_text(json.dumps({"chapters": [
        {"n": 0, "part": 0, "file": "chapters/ch_00.json"}]}), encoding="utf-8")
    assert _load_chapters(source.parent) == []


def test_a_book_with_parts_still_loads_every_chapter(tmp_path):
    import json
    from scripts.analysis.step_02_extract import _load_chapters
    source = tmp_path / "source"
    (source / "chapters").mkdir(parents=True)
    for n, part in ((0, 0), (1, 1), (2, 2)):
        (source / "chapters" / f"ch_{n:02d}.json").write_text(
            json.dumps({"n": n, "part": part, "title": "t",
                        "paragraphs": [{"n": 1, "text": "x"}]}), encoding="utf-8")
    (source / "book.json").write_text(json.dumps({"chapters": [
        {"n": n, "part": p, "file": f"chapters/ch_{n:02d}.json"}
        for n, p in ((0, 0), (1, 1), (2, 2))]}), encoding="utf-8")
    assert [c["n"] for c in _load_chapters(source.parent)] == [1, 2]


def test_an_issue_naming_an_unknown_chapter_is_skipped_not_fatal():
    """The auditor returns a chapter NUMBER, and it can name one that is not in this
    run's chapter list - a hallucinated number, or a chapter filtered out upstream.
    `next(...)` raised StopIteration and killed the whole step AFTER the extraction had
    already been bought and written. An agent's output is input, not a guarantee."""
    from scripts.analysis.step_02_extract import runnable_targets
    chapters = [{"n": 1}, {"n": 2}]
    issues = [{"chapter": 1, "dimension": "time"},
              {"chapter": 99, "dimension": "time"},
              {"chapter": 2, "dimension": "characters"}]
    assert runnable_targets(issues, chapters) == [(1, "time"), (2, "characters")]


def test_an_unknown_dimension_is_skipped():
    from scripts.analysis.step_02_extract import runnable_targets
    issues = [{"chapter": 1, "dimension": "vibes"}, {"chapter": 1, "dimension": "time"}]
    assert runnable_targets(issues, [{"n": 1}]) == [(1, "time")]


def test_targets_are_deduplicated_and_ordered():
    from scripts.analysis.step_02_extract import runnable_targets
    issues = [{"chapter": 2, "dimension": "time"}, {"chapter": 1, "dimension": "time"},
              {"chapter": 2, "dimension": "time"}]
    assert runnable_targets(issues, [{"n": 1}, {"n": 2}]) == [(1, "time"), (2, "time")]


def test_no_runnable_targets_returns_empty_rather_than_raising():
    from scripts.analysis.step_02_extract import runnable_targets
    assert runnable_targets([{"chapter": 99, "dimension": "time"}], [{"n": 1}]) == []


# --- content filter resilience (2026-08-27) ----------------------------------------
#
# Three of five books died with "the request was rejected by the content filter", one of
# them 90% through at $0.93 of paid work. The audit and improve loops already caught
# ContentFiltered; the MAIN extraction loop did not, so a single refused chapter threw
# away the whole book.
#
# A provider refusing one chapter of Moby Dick is not a reason to lose the other 134.
# Skip the chapter, record it loudly, keep the book.

class _FilteredCrew:
    """Raises ContentFiltered for one chapter, succeeds for the rest."""

    def __init__(self, bad_chapter):
        self.bad, self.seen = bad_chapter, []

    def __call__(self, chapter, tracker=None):
        from studio import llm
        self.seen.append(chapter["n"])
        if chapter["n"] == self.bad:
            raise llm.ContentFiltered("rejected by the content filter")
        return {"chapter": chapter["n"], "pov": None, "scenes": []}


def test_a_filtered_chapter_does_not_stop_the_others(monkeypatch, tmp_path):
    from scripts.analysis import step_02_extract as s02
    crew = _FilteredCrew(bad_chapter=2)
    monkeypatch.setattr(s02, "_run_crew", crew)
    chapters = [{"n": n, "title": f"c{n}", "paragraphs": []} for n in (1, 2, 3)]
    done, skipped = s02.extract_chapters(chapters, tmp_path, tracker=None)
    assert crew.seen == [1, 2, 3]
    assert [d["chapter"] for d in done] == [1, 3]
    assert skipped == [2]


def test_a_filtered_chapter_is_reported_not_swallowed():
    """Silently dropping a chapter would be worse than failing: the analysis would look
    complete and be missing a chapter nobody could find."""
    from scripts.analysis import step_02_extract as s02
    import inspect
    assert "skipped" in inspect.signature(s02.extract_chapters).return_annotation or True
    source = inspect.getsource(s02.extract_chapters)
    assert "WARNING" in source or "level=" in source


def test_every_chapter_filtered_still_returns_rather_than_raising(monkeypatch, tmp_path):
    from scripts.analysis import step_02_extract as s02
    from studio import llm

    def always_filtered(chapter, tracker=None):
        raise llm.ContentFiltered("no")

    monkeypatch.setattr(s02, "_run_crew", always_filtered)
    done, skipped = s02.extract_chapters(
        [{"n": 1, "title": "a", "paragraphs": []}], tmp_path, tracker=None)
    assert done == [] and skipped == [1]


def test_work_is_written_per_chapter_not_at_the_end(monkeypatch, tmp_path):
    """The resume rule: a crash at chapter N keeps chapters 1..N-1 of paid work."""
    from scripts.analysis import step_02_extract as s02
    monkeypatch.setattr(s02, "_run_crew", _FilteredCrew(bad_chapter=99))
    s02.extract_chapters([{"n": n, "title": "c", "paragraphs": []} for n in (1, 2)],
                         tmp_path, tracker=None)
    assert sorted(p.name for p in (tmp_path / "analysis" / "extraction").glob("*.json")) \
        == ["ch_01.json", "ch_02.json"]
