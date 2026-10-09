"""ep24 (2026-10-09 03:45Z): QC failed master_iter5 on the edit gate's head rule,
fixed minutes later -- but a recut of unchanged inputs makes the same bytes,
and step 11 reuses a report for the same bytes, pass or FAIL.  The fixed rule
could never reach the master.  A QC report is reused only while the code that
measured it is the code now (the take DQ cache's rule, A75)."""
from __future__ import annotations

import json
from types import SimpleNamespace

from scripts.episode import step_11_qc as step
from studio import youtube_publish as yp


def _ctx(tmp_path, report: dict):
    home = tmp_path / "ep24"
    (home / "cut").mkdir(parents=True)
    master, qc = step.pair(home, "r2v")
    master.write_bytes(b"master bytes")
    qc.write_text(json.dumps(report | {"sha8": yp.sha8(master)}), encoding="utf-8")
    runs = []
    ctx = SimpleNamespace(home=home, log=lambda *a, **k: None,
                          run_script=lambda script, *a, **k: runs.append(script))
    return ctx, runs


def test_a_report_by_this_code_is_reused(tmp_path):
    ctx, runs = _ctx(tmp_path, {"passed": True, "measures_sha8": step.qc_measures_sha8()})
    assert step.qc_report(ctx, ["--engine=r2v"])["passed"] is True
    assert runs == []


def test_a_report_by_older_code_is_measured_again(tmp_path):
    ctx, runs = _ctx(tmp_path, {"passed": False, "measures_sha8": "00000000"})
    try:
        step.qc_report(ctx, ["--engine=r2v"])
    except SystemExit:
        pass
    assert runs and runs[0].endswith("qc.py")
