"""Jekyll ep04, 2026-10-27: the first live judged cut was refused -- `edit: FAIL | segments off 1/27`
(T02 mean 1.668 over SEGMENT_MEAN_CUT 1.6, a cap fitted on ep03's cut alone) and `lines heard not
measured`, `failed: line_unheard`.

The lines were not skipped by the cut path: QC hears the lines LAST, only on a file whose cheap rows
pass (C3_verdict #2), on the master and on the cut alike, and an unmeasured line is not a heard line.
The edit row failed first, so the ear never ran.  The refusal now says the lines were not measured
rather than unheard.  The cap is refit from the ratio between the cut and the av3 master of the SAME
episode (tests/fixtures/cut_segment_means.json, measured 2026-10-27 by qc.edit_report): ep03's
28 segments read 0.270-0.778 of their av3 master's mean (median 0.556); the av3 cap 2.5 times the
largest ratio is 1.95.  ep04's cut (0.777-1.668) and ep03's (0.500-1.362) sit under it."""
from __future__ import annotations

import json
from pathlib import Path

from tests.test_qc_fails_fast_before_the_ear import LINES, Ear, _wire, qc

MEANS = json.loads((Path(__file__).parent / "fixtures" / "cut_segment_means.json").read_text(encoding="utf-8"))


def test_a_cut_whose_cheap_rows_pass_hears_every_line(monkeypatch, tmp_path):
    _wire(monkeypatch, tmp_path)
    ear = Ear()
    report = qc.measure("b", 3, "r2v", ear, at_cut=True)
    assert ear.calls == len(LINES) and report["lines_measured"] is True and report["passed"] is True


def test_a_cut_whose_edit_fails_is_not_heard_and_the_refusal_says_not_measured():
    from scripts.episode import step_11_qc
    report = {"lufs_ok": True, "tp_ok": True, "missing_cuts": [], "seconds": 150.0, "title_card": True,
              "edit": {"measured": True, "ok": False}, "lines": None, "lines_measured": False}
    words = step_11_qc.fail_words(report)
    assert "edit" in words and "line_unheard (not measured" in words


def test_the_cut_cap_is_the_av3_cap_times_the_measured_cut_to_master_ratio():
    from studio import edit_gate
    master, cut = MEANS["ep03_master_av3"], MEANS["ep03_cut"]
    ratio = max(cut[k] / master[k] for k in master)
    assert abs(edit_gate.SEGMENT_MEAN_CUT - round(edit_gate.SEGMENT_MEAN_AV3 * ratio, 2)) < 0.01
    assert edit_gate.segment_cap("cut") == edit_gate.SEGMENT_MEAN_CUT


def test_both_live_cuts_read_under_the_cap():
    from studio import edit_gate
    for name in ("ep03_cut", "ep04_cut"):
        assert max(MEANS[name].values()) <= edit_gate.segment_cap("cut"), name
    assert MEANS["ep04_cut"]["2"] == 1.668, "the segment that refused ep04"
