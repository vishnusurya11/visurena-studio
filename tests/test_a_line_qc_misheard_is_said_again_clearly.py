"""ep27 (2026-10-10 22:45Z): QC failed the master on one line -- 'Nights bring
back the black powder.' heard as 'Night spring back...' (0.333 against the wall);
the recording itself had already been heard as 'Nights spring back' and passed
the ear narrowly.  A recut cannot change it (same audio) and a re-say kept by
voice fit cannot target it.  A line QC heard wrong is said again by the record
step, ONCE, and the try the ear hears most clearly is kept."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("say_lines_clear", ROOT / "scripts" / "episode" / "say_lines.py")
say = importlib.util.module_from_spec(spec)
sys.modules["say_lines_clear"] = say
spec.loader.exec_module(say)


def _wavs(tmp_path):
    wav = tmp_path / "l15.wav"
    wav.write_bytes(b"new")
    wav.with_suffix(".prev.wav").write_bytes(b"old")
    return wav


def test_a_clearer_try_wins_when_clarity_is_asked(tmp_path):
    wav = _wavs(tmp_path)
    new = {"error_rate": 0.0, "similarity": 0.70, "passed": True}
    old = {"error_rate": 0.167, "similarity": 0.80, "passed": True}
    assert say.keep_best(new, old, wav, fit=(0.70, 0.80), clarity=True) is new


def test_a_muddier_try_loses_when_clarity_is_asked(tmp_path):
    wav = _wavs(tmp_path)
    new = {"error_rate": 0.33, "similarity": 0.90, "passed": True}
    old = {"error_rate": 0.167, "similarity": 0.80, "passed": True}
    assert say.keep_best(new, old, wav, fit=(0.9, 0.8), clarity=True)["error_rate"] == 0.167


def _ctx(tmp_path, qc_lines, said=None):
    from scripts.episode import step_04_record as step
    home = tmp_path / "ep27"
    (home / "audio" / "lines").mkdir(parents=True)
    (home / "review").mkdir()
    (home / "plan.json").write_text(json.dumps({"lines": [{"index": 15}]}), encoding="utf-8")
    (home / "audio" / "lines" / "lines.json").write_text(json.dumps([{"index": 15, "seconds": 2.4}]), encoding="utf-8")
    (home / "review" / "speaker_check.json").write_text(json.dumps({"n": {"ok": True, "under": []}}), encoding="utf-8")
    (home / "qc_r2v.json").write_text(json.dumps({"lines": qc_lines}), encoding="utf-8")
    if said is not None:
        (home / "review" / step.QC_RESAID).write_text(json.dumps(said), encoding="utf-8")
    calls = []
    ctx = SimpleNamespace(home=home, book_dir=tmp_path, number=27, extra=[],
                          run_script=lambda script, *a, **k: calls.append((script.rsplit("/", 1)[-1],) + a))
    return step, ctx, calls


def test_a_line_qc_misheard_keeps_the_record_step_open_once(tmp_path):
    misheard = [{"index": 15, "passed": False, "error_rate": 0.333}]
    step, ctx, _ = _ctx(tmp_path, misheard)
    assert step.qc_misheard(ctx) == [15]
    assert step.done(ctx) is False
    step, ctx, _ = _ctx(tmp_path / "b", misheard, said=[15])
    assert step.done(ctx) is True                      # said again once: QC decides


def test_the_record_step_says_the_misheard_line_again_for_clarity(tmp_path, monkeypatch):
    step, ctx, calls = _ctx(tmp_path, [{"index": 15, "passed": False, "error_rate": 0.333}])
    monkeypatch.setattr(step, "voiceless", lambda ctx: [])
    step.run(ctx)
    assert ("say_lines.py", "--redo=15", "--clear") in calls
    assert json.loads((ctx.home / "review" / step.QC_RESAID).read_text(encoding="utf-8")) == [15]
