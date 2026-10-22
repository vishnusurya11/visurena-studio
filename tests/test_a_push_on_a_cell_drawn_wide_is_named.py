"""A push planned on a panel drawn a size wider than its plan is named (advisory; shot framework B-4, n = 1).

Bench B1 (2026-10-21): ep01 shot 15 was planned medium close, and its panel was drawn head to boots (the
panel gate's G-FRAME record: face 0.119 of the frame, under the 0.15 medium-close floor, frame_advisory).
The push therefore travelled full -> medium and reached end/first face 2.23 against the 1.6 cap, crown
cut.  The cell sets the framing, not the plan words.  The record is the panel gate's own G-FRAME row,
so the note costs nothing; it never flags or fails the panel."""
from __future__ import annotations

from scripts.episode import panel_check
from studio import panel_dq

T15 = {"face_h": 0.119, "planned_size": "medium_close", "frame_advisory": True}
"""ep01 storyboard/panel_dq.json, shot 15, as the panel gate recorded it."""


def test_ep01_t15_full_cell_planned_mc():
    note = panel_dq.push_on_wide_cell(T15, "push_slow")
    assert "push" in note["push_note"] and "wider" in note["push_note"]


def test_a_locked_shot_or_a_cell_at_its_size_gets_no_note():
    assert panel_dq.push_on_wide_cell(T15, "locked") == {}
    assert panel_dq.push_on_wide_cell({**T15, "frame_advisory": False}, "push_slow") == {}
    assert panel_dq.push_on_wide_cell({}, "push_slow") == {}


def test_the_panel_check_records_the_note_beside_the_frame_record():
    found = [{"h": 0.119, "score": 0.99}]
    shot = type("S", (), {"faces": ["lead"], "size": "medium_close", "frame": "Medium close on the lead",
                          "at_rest": "", "motion": "The camera pushes in toward his face across the whole shot"})()
    row = panel_check.framing_rows(shot, found)
    assert row["frame_advisory"] and "push_note" in row
    assert "push_note" not in panel_check.framing_rows(
        type("L", (), {**vars(type(shot)), "motion": "The camera holds a locked-off frame"})(), found)
