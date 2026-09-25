"""A prose line that names a take and a fault word becomes a CANDIDATE row.

The row is `verdict_by: unverified` with the file and line it was read from,
so a person can open the artefact and confirm it into the owner overlay.  A
line that names a take and no fault word is not a row.  A stored dq record
becomes one default-pass row for the kept take and one agent-fault row per
losing attempt, class from the attempt's filename when it carries one.
"""
import json
from pathlib import Path

from scripts.calibration import harvest_labels as hl

FIXTURES = Path(__file__).parent / "fixtures" / "casebook"
CODEX = "00000000000000"


def test_a_line_with_a_take_and_a_fault_word_is_a_candidate():
    text = (FIXTURES / "story_snippet.md").read_text(encoding="utf-8")
    rows = hl.candidates(text, "episodes/ep02/story.md", CODEX, unit_hint="ep02")
    by_path = {r.path: r for r in rows}
    slid = by_path["episodes/ep02/takes/r2v/T05.mp4"]
    assert slid.verdict_by == "unverified" and slid.verdict == "fault"
    assert slid.fault_class == "anchored_slide" and slid.kind == "take"
    assert slid.source == "episodes/ep02/story.md#L5"
    assert by_path["episodes/ep02/takes/r2v/T07.mp4"].fault_class == "lettering"


def test_a_take_without_a_fault_word_is_not_a_row():
    text = (FIXTURES / "story_snippet.md").read_text(encoding="utf-8")
    rows = hl.candidates(text, "episodes/ep02/story.md", CODEX, unit_hint="ep02")
    assert "episodes/ep02/takes/r2v/T09.mp4" not in {r.path for r in rows}


def test_a_take_named_without_its_unit_takes_the_hint():
    text = (FIXTURES / "story_snippet.md").read_text(encoding="utf-8")
    rows = hl.candidates(text, "episodes/ep02/story.md", CODEX, unit_hint="ep02")
    masthead = [r for r in rows if r.path.endswith("T11.mp4")]
    assert masthead and masthead[0].unit == "ep02" and masthead[0].fault_class == "wrong_letters"


def test_a_stored_dq_record_becomes_a_kept_row_and_attempt_rows():
    dq = json.loads((FIXTURES / "dq_rows.json").read_text(encoding="utf-8"))
    planned = {"motion": "The camera pushes in a hand's breadth", "size": "close", "faces": 1, "daylight": False}
    rows = hl.take_rows(CODEX, "ep02", dq, planned, "episodes/ep02/takes/r2v/T05.dq.json", "git:0000000")
    by_path = {r.path: r for r in rows}
    kept = by_path["episodes/ep02/takes/r2v/T05.mp4"]
    assert kept.verdict == "pass" and kept.verdict_by == "default"
    assert kept.machine["take_dq"]["score"] == 60.0 and kept.machine["take_dq"]["planned"]["size"] == "close"
    lost = by_path["episodes/ep02/takes/r2v/attempts/T05_fail1.mp4"]
    assert lost.verdict == "fault" and lost.verdict_by == "agent" and lost.fault_class == "unknown"
    named = by_path["episodes/ep02/takes/r2v/attempts/T05_fail2_wrong_lettering.mp4"]
    assert named.fault_class == "wrong_letters"
    assert all(r.machine_version == "git:0000000" for r in rows)
