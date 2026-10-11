"""At a spent clock a verdict on the same bytes stands though the code moved
(ruled 2026-10-11 for the owner, for veto; C3_p90_residual §4.3).

Below the ceiling a report holds only under its measuring code (2026-10-08:
the fixed letterbox measure never reached ep21's T27/T30).  Past it, a
re-judge is a REPEAT -- every ladder is terminal, so it can change only a
flag -- and ep21 paid ~16 min after its crossing re-judging takes on moved
code (runs 18-19).  So past the ceiling:
- a take's dq report on the same bytes stands, pass or fail (take_dq.cached);
- a PASSING QC report on the same master bytes stands; a FAIL is re-measured,
  because a moved rule may clear it and a SAFETY fail stops the episode.
Stale bytes are never served: the key is still the take's or master's sha8."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

from tests.test_a_spent_clock_ships_flagged_and_never_parks import GOOD, _qc_ctx, step09, step11

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "episode"))
import take_dq  # noqa: E402


def _take(tmp_path, measures: str) -> tuple[Path, dict]:
    take = tmp_path / "T03.mp4"
    take.write_bytes(b"the very bytes")
    report = {"take_sha8": take_dq.take_sha8(take), "measures_sha8": measures, "score": 61.0}
    (tmp_path / "T03.dq.json").write_text(json.dumps(report), encoding="utf-8")
    return take, report


def test_a_take_report_under_old_code_stands_only_past_the_ceiling(tmp_path):
    take, report = _take(tmp_path, "00000000")
    assert take_dq.cached(tmp_path, 3, take) is None
    assert take_dq.cached(tmp_path, 3, take, any_code=True) == report
    take.write_bytes(b"other bytes")                       # stale bytes are never served
    assert take_dq.cached(tmp_path, 3, take, any_code=True) is None


def test_step_09_tells_the_dq_pass_when_the_clock_is_spent():
    from studio.run_budget import EPISODE_SHARES, Budget
    spent, fresh = Budget(18000, EPISODE_SHARES, clock=lambda: 0.0), Budget(18000, EPISODE_SHARES, clock=lambda: 0.0)
    spent.charge(18001.0)
    assert step09.dq_flags(SimpleNamespace(budget=spent)) == ["--ceiling-spent"]
    assert step09.dq_flags(SimpleNamespace(budget=fresh)) == []
    assert step09.dq_flags(SimpleNamespace()) == []


def _moved(ctx, path):
    doc = json.loads(path.read_text(encoding="utf-8"))
    path.write_text(json.dumps({**doc, "measures_sha8": "00000000"}), encoding="utf-8")
    ran = []
    ctx.run_script = lambda *a, **k: ran.append(a)
    return ran


def test_a_passing_qc_report_under_old_code_stands_past_the_ceiling(tmp_path):
    ctx, path = _qc_ctx(tmp_path, {**GOOD, "passed": True}, spent=True)
    ran = _moved(ctx, path)
    assert step11.qc_report(ctx, ["--engine=r2v"])["passed"] is True
    assert ran == []


def test_below_the_ceiling_a_passing_report_under_old_code_is_measured_again(tmp_path):
    ctx, path = _qc_ctx(tmp_path, {**GOOD, "passed": True}, spent=False)
    ran = _moved(ctx, path)
    step11.qc_report(ctx, ["--engine=r2v"])
    assert ran and ran[0][0] == "scripts/episode/qc.py"


def test_a_failing_qc_report_under_old_code_is_measured_again_past_the_ceiling(tmp_path, monkeypatch):
    from studio import audit_rows
    monkeypatch.setattr(audit_rows, "append", lambda book, row: None)
    ctx, path = _qc_ctx(tmp_path, {**GOOD, "sound": [{"ok": False}], "passed": False}, spent=True)
    ran = _moved(ctx, path)
    step11.qc_report(ctx, ["--engine=r2v"])
    assert ran and ran[0][0] == "scripts/episode/qc.py"
