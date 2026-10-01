"""Five-hour plan fix 3 (2026-09-30): QC's ~9 min pass runs once per set of
master bytes.  ep14 ran qc 8x; a FAILED report on an unchanged master was
discarded by done() and the whole measurement re-run with no assemble in
between (ep14 01:59 and 02:11; ep13 three pairs).  Now qc_report reuses a
report whose sha8 matches the master -- a pass returns, a fail refuses -- and
only a recut (new bytes) measures again."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
loader = importlib.util.spec_from_file_location("step11", ROOT / "scripts" / "episode" / "step_11_qc.py")
step11 = importlib.util.module_from_spec(loader)
sys.modules["step11"] = step11
loader.loader.exec_module(step11)

from studio import youtube_publish as yp  # noqa: E402


class Ctx:
    def __init__(self, home: Path):
        self.home, self.ran, self.said = home, [], []

    def run_script(self, script, *extra, **kw):
        self.ran.append(script)

    def log(self, text):
        self.said.append(text)


def room(tmp_path: Path, passed: bool, matching: bool) -> Ctx:
    (tmp_path / "cut").mkdir(parents=True)
    master = tmp_path / "cut" / "master_r2v.mp4"
    master.write_bytes(b"the master bytes")
    sha = yp.sha8(master) if matching else "00000000"
    (tmp_path / "qc_r2v.json").write_text(json.dumps({"passed": passed, "sha8": sha, "seconds": 160.0}),
                                          encoding="utf-8")
    return Ctx(tmp_path)


def test_a_passed_report_for_these_bytes_is_reused_without_a_run(tmp_path):
    ctx = room(tmp_path, passed=True, matching=True)
    report = step11.qc_report(ctx, ["--engine=r2v"])
    assert report["passed"] and ctx.ran == []
    assert any("reused" in s for s in ctx.said)


def test_a_failed_report_for_these_bytes_refuses_without_a_run(tmp_path):
    ctx = room(tmp_path, passed=False, matching=True)
    with pytest.raises(SystemExit, match="exact bytes"):
        step11.qc_report(ctx, ["--engine=r2v"])
    assert ctx.ran == []


def test_new_bytes_are_measured(tmp_path):
    ctx = room(tmp_path, passed=True, matching=False)
    with pytest.raises(SystemExit):        # the stubbed run writes nothing, so the refusal names that
        step11.qc_report(ctx, ["--engine=r2v"])
    assert ctx.ran == ["scripts/episode/qc.py"]
