"""A catch written as "epNN 33-40 s" resolves to the takes on screen then.

The timeline (`placed.json`) is the only map from a second to a shot; a take
is named after its shot.  A span that straddles two shots names both takes.
"""
import json
from pathlib import Path

from scripts.calibration import harvest_labels as hl

FIXTURES = Path(__file__).parent / "fixtures" / "casebook"
CODEX = "00000000000000"


def placed():
    return json.loads((FIXTURES / "placed.json").read_text(encoding="utf-8"))


def test_a_span_names_every_take_on_screen():
    assert hl.takes_at(placed(), 33.0, 40.0) == ["T04", "T05"]


def test_a_span_inside_one_shot_names_one_take():
    assert hl.takes_at(placed(), 25.0, 28.0) == ["T02"]


def test_a_timestamp_line_becomes_a_row_per_take():
    text = (FIXTURES / "story_snippet.md").read_text(encoding="utf-8")
    rows = hl.timestamp_rows(text, "docs/audit/fixture.md", CODEX, lambda unit: placed() if unit == "ep02" else None)
    assert [r.path for r in rows] == ["episodes/ep02/takes/r2v/T04.mp4", "episodes/ep02/takes/r2v/T05.mp4"]
    assert {r.fault_class for r in rows} == {"stacked_pictures"}
    assert {r.verdict_by for r in rows} == {"unverified"}
    assert rows[0].source == "docs/audit/fixture.md#L10"


def test_a_unit_without_a_timeline_yields_no_row():
    text = (FIXTURES / "story_snippet.md").read_text(encoding="utf-8")
    assert hl.timestamp_rows(text, "docs/audit/fixture.md", CODEX, lambda unit: None) == []
