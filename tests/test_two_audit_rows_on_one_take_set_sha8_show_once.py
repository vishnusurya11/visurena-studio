"""Two terminal rows of one gate on one take-set sha8 are one terminal seen twice (the ladder
re-signs a verdict on every resume): the sheet shows the newest once."""
from __future__ import annotations

from pathlib import Path

from scripts.audit import sheet
from studio.audit_rows import AuditRow


def row(sha8, ts, gate="EYE_TAKES", note="n"):
    return AuditRow(unit="ep01", gate=gate, judge="judge:take_eye@1", sha8=sha8, terminal="keep_best",
                    artefact="episodes/ep01/takes/r2v/eye_" + sha8 + ".json", ts=ts,
                    faults=[{"kind": "warp", "where": "T01", "note": note}])


def test_one_sha8_shows_once_the_newest():
    out = sheet.deduped([row("b368ae93", "2026-10-19T01:00:00Z", note="old"),
                         row("b368ae93", "2026-10-19T02:00:00Z", note="new")])
    assert len(out) == 1 and out[0].faults[0]["note"] == "new"


def test_other_sha8_or_gate_stay():
    rows = [row("a", "1"), row("b", "2"), row("a", "3", gate="PLAN")]
    assert len(sheet.deduped(rows)) == 3


def test_a_row_with_no_sha8_is_never_merged():
    assert len(sheet.deduped([row("", "1"), row("", "2")])) == 2


def test_the_page_counts_the_deduped_rows(tmp_path):
    rows = [row("b368ae93", "1"), row("b368ae93", "2")]
    page = sheet.page(Path(tmp_path), "ep01", rows)
    assert "<b>1</b> flagged" in page
