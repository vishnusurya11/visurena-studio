"""A qc refusal names the rows that failed (timeline debate 2026-10-18, P3; owner go): the 45
'REFUSED: qc FAIL in qc_r2v.json' rows in the events table said nothing of why, and the report
is overwritten on the next pass -- so whether a cut gate before the upscale would pay could not
be measured.  The refusal now carries `qc.failed_rows`; step_11_qc.py is outside QC_MEASURES, so
no stored report is re-measured.  $0: tmp files, no ffmpeg, no model."""
from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from scripts.episode import step_11_qc as s11
from studio import youtube_publish as yp


def test_fail_words_name_the_failed_rows():
    report = {"lufs_ok": False, "tp_ok": True, "edit": {"measured": True, "ok": True}, "title_card": True,
              "sound": [], "speech_over_gap_db": 20.0, "seconds": 150.0}
    assert "loudness" in s11.fail_words(report)


def test_the_reused_fail_names_its_rows(tmp_path):
    home = tmp_path / "ep01"
    master, qc = s11.pair(home, s11.ENGINE)
    master.parent.mkdir(parents=True)
    master.write_bytes(b"master bytes")
    qc.write_text(json.dumps({"sha8": yp.sha8(master), "measures_sha8": s11.qc_measures_sha8(), "passed": False,
                              "lufs_ok": False, "tp_ok": True, "title_card": True}), encoding="utf-8")
    ctx = SimpleNamespace(home=home, budget=None, log=lambda *a, **k: None)
    with pytest.raises(SystemExit) as got:
        s11.qc_report(ctx, [])
    assert "loudness" in str(got.value) and str(got.value).startswith("REFUSED: qc FAIL")


def test_qc_measures_still_excludes_the_step():
    # the change must not re-measure every stored report
    assert "scripts/episode/step_11_qc.py" not in s11.QC_MEASURES
