"""C3_verdict #2 (T2): QC measures its cheap rows first.

10 of 14 QC-fail runs over ep19-27 failed on a cheap row -- loudness, a cue,
the edit -- after Whisper had read every line.  On the ep27 master each cheap
row takes 0.1-17 s (edit gate 17.3 s, the rest under 3 s; none over 30 s, so
none moved after the ear).  A master whose cheap rows fail is written with
`lines: null, lines_measured: false` and never transcribed; an unmeasured
line is NOT a heard line (`all([])` would have read True)."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("ep_qc_fast", ROOT / "scripts" / "episode" / "qc.py")
qc = importlib.util.module_from_spec(spec)
sys.modules["ep_qc_fast"] = qc
spec.loader.exec_module(qc)

OLD_KEYS = {"master", "sha8", "measures_sha8", "seconds", "planned_seconds", "title_card", "lufs", "lufs_ok",
            "true_peak", "tp_ok", "planned_cuts", "seen_cuts", "missing_cuts", "internal_cuts", "lines",
            "speech_over_gap_db", "longest_gap_s", "speech_s", "edit", "internal_cut_rows", "sound", "takes",
            "sheets", "passed"}
LINES = [{"index": i, "at": 2.0 * i, "seconds": 1.5, "text": "the pit", "shot": i} for i in range(3)]


class Ear:
    """A FakeTranscriber that counts its calls and hears every line right."""

    def __init__(self):
        self.calls = 0

    def __call__(self, clip):
        self.calls += 1
        return "the pit"


def _wire(monkeypatch, tmp_path, lufs=-14.0, sound_ok=True):
    placed = {"duration_s": 7.0, "shots": [{"index": i, "t_start": 2.0 * i} for i in range(3)]}
    inputs = SimpleNamespace(book=tmp_path, master=tmp_path / "master.mp4", work=tmp_path, placed=placed,
                             take_dir=tmp_path, lines=LINES, records=[], episode=None, number=3)
    monkeypatch.setattr(qc, "load_inputs", lambda book_id, number, engine: inputs)
    for name, value in {"integrated": lufs, "true_peak": -2.0, "clip_seconds": 160.0, "qc_code_sha8": "c0de0000",
                        "speech_band": 12.0}.items():
        monkeypatch.setattr(qc, name, lambda *a, _v=value, **k: _v)
    monkeypatch.setattr(qc, "seen_cuts", lambda master: [2.0, 4.0])
    monkeypatch.setattr(qc.yp, "sha8", lambda path: "abcd1234")
    monkeypatch.setattr(qc.episode_home, "relative", lambda book, path: "cut/master.mp4")
    monkeypatch.setattr(qc, "edit_report", lambda *a, **k: {"ok": True, "measured": True, "cuts": []})
    monkeypatch.setattr(qc.episode_sound, "presence", lambda *a: [{"ok": sound_ok}])
    monkeypatch.setattr(qc, "takes_rollup", lambda d: {"unjudged": []})
    monkeypatch.setattr(qc, "sheets_rollup", lambda b, book: [])
    monkeypatch.setattr(qc, "window", lambda master, at, seconds, out: out)
    monkeypatch.setattr(qc, "title_card_on_disk", lambda book, number: True)


def test_a_failed_cheap_row_never_calls_the_ear(monkeypatch, tmp_path):
    _wire(monkeypatch, tmp_path, sound_ok=False)
    ear = Ear()
    report = qc.measure("b", 3, "r2v", ear)
    assert ear.calls == 0
    assert report["lines"] is None and report["lines_measured"] is False and report["passed"] is False


def test_a_loudness_fail_is_fast_too(monkeypatch, tmp_path):
    _wire(monkeypatch, tmp_path, lufs=-30.0)
    ear = Ear()
    assert qc.measure("b", 3, "r2v", ear)["lines_measured"] is False and ear.calls == 0


def test_a_passing_master_is_heard_line_by_line(monkeypatch, tmp_path):
    _wire(monkeypatch, tmp_path)
    ear = Ear()
    report = qc.measure("b", 3, "r2v", ear)
    assert ear.calls == len(LINES) and report["passed"] is True and report["lines_measured"] is True


def test_the_report_keys_are_todays_plus_lines_measured(monkeypatch, tmp_path):
    _wire(monkeypatch, tmp_path)
    assert set(qc.measure("b", 3, "r2v", Ear())) == OLD_KEYS | {"lines_measured"}


GOOD = {"title_card": True, "lufs_ok": True, "tp_ok": True, "missing_cuts": [], "lines": [{"passed": True}],
        "edit": {"ok": True, "measured": True}, "seconds": 160.0}


@pytest.mark.parametrize("lines", [None, []])
def test_unmeasured_lines_are_not_heard(lines):
    assert qc.verdict(GOOD)
    assert not qc.verdict({**GOOD, "lines": None})
    assert not qc.verdict({**GOOD, "lines": lines, "lines_measured": False})


def test_a_fast_fail_report_is_reused_only_on_the_same_bytes_and_code(tmp_path):
    from scripts.episode import step_11_qc as step
    from tests.test_a_qc_report_holds_only_under_its_code import _ctx
    fast = {"passed": False, "lines": None, "lines_measured": False}
    ctx, runs = _ctx(tmp_path / "same", fast | {"measures_sha8": step.qc_measures_sha8()})
    with pytest.raises(SystemExit, match="these exact bytes"):
        step.qc_report(ctx, ["--engine=r2v"])
    assert runs == []
    ctx, runs = _ctx(tmp_path / "moved", fast | {"measures_sha8": "00000000"})
    with pytest.raises(SystemExit):
        step.qc_report(ctx, ["--engine=r2v"])
    assert runs and runs[0].endswith("qc.py")
