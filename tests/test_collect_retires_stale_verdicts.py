"""Retirement at the source: the moment collect() writes a fresh take's
bytes, the verdicts judged on the OLD bytes are unlinked, so no existence
check anywhere can mistake a pre-retake verdict for a current one."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("takes_retire", ROOT / "scripts" / "episode" / "takes_r2v.py")
takes = importlib.util.module_from_spec(_spec)
sys.modules["takes_retire"] = takes
_spec.loader.exec_module(takes)


@pytest.fixture()
def rendered(tmp_path, monkeypatch):
    video = tmp_path / "rendered.mp4"
    video.write_bytes(b"fresh take bytes")
    monkeypatch.setattr(takes, "wait_record", lambda pid, timeout: {})
    monkeypatch.setattr(takes, "outputs_of", lambda record: [video])
    monkeypatch.setattr(takes, "clip_seconds", lambda path: 4.0)
    return tmp_path / "takes" / "T05.mp4"


def test_stale_sidecars_are_gone_after_collect(tmp_path, rendered, monkeypatch):
    out = rendered
    out.parent.mkdir(parents=True)
    out.with_suffix(".dq.json").write_text("{}", encoding="utf-8")
    out.with_suffix(".content.json").write_text("{}", encoding="utf-8")
    takes.collect({"index": 5}, "pid-5", out)
    assert out.read_bytes() == b"fresh take bytes"
    assert not out.with_suffix(".dq.json").exists()
    assert not out.with_suffix(".content.json").exists()


def test_absent_sidecars_do_not_raise(rendered):
    out = rendered
    record = takes.collect({"index": 5}, "pid-5", out)
    assert out.exists() and record["measured_seconds"] == 4.0


def test_retire_verdicts_unlinks_both_and_tolerates_absence(tmp_path):
    out = tmp_path / "T07.mp4"
    out.with_suffix(".dq.json").write_text("{}", encoding="utf-8")
    takes.retire_verdicts(out)
    takes.retire_verdicts(out)                      # second call: nothing there, no raise
    assert not out.with_suffix(".dq.json").exists()
