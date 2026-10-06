"""Step 05's one-shot auto-trim: a measured speech-hole refusal under
UNRENDERED takes gets one bounded trim, one respot+timeline re-run, the free
battery, and the PLAN JUDGE's re-sign -- never the owner's name, never a
second loop.  Rendered takes refuse untrimmed (a plan under rendered takes is
never edited); a still-refused re-run carries speech_gap.refusal's own text."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
_spec = importlib.util.spec_from_file_location(
    "step05", ROOT / "scripts" / "episode" / "step_05_timeline.py")
mod = importlib.util.module_from_spec(_spec)
sys.modules["step05"] = mod
_spec.loader.exec_module(mod)

from test_hole_gate_measures_like_step05 import episode_with_wordless_run  # noqa: E402

WHY = "REFUSED: a 8.00 s hole in speech from 2.25 s (shot 1) against the 6.0 s wall; x"


def ctx_of(tmp_path, battery=(0, "VERDICT      : clean")) -> SimpleNamespace:
    home = tmp_path / "book" / "episodes" / "ep01"
    home.mkdir(parents=True)
    calls = {"run": [], "battery": []}
    ctx = SimpleNamespace(book_dir=tmp_path / "book", number=1, home=home, calls=calls)
    ctx.run_script = lambda script, **kw: calls["run"].append(script)
    ctx.capture_script = lambda script, *a: (calls["battery"].append(script), battery)[1]
    return ctx


def test_rendered_takes_refuse_untrimmed(tmp_path, monkeypatch):
    ctx = ctx_of(tmp_path)
    (ctx.home / "takes" / "r2v").mkdir(parents=True)
    (ctx.home / "takes" / "r2v" / "T01.mp4").touch()
    monkeypatch.setattr(mod, "trimmed", lambda *a: pytest.fail("a rendered plan was edited"))
    with pytest.raises(SystemExit, match="8.00 s hole"):
        mod.autotrim(ctx, WHY)
    assert ctx.calls["run"] == []                              # no re-run either


def test_nothing_trimmable_refuses_with_the_original_text(tmp_path, monkeypatch):
    ctx = ctx_of(tmp_path)
    monkeypatch.setattr(mod, "placed_of", lambda *a: {"lines": []})
    monkeypatch.setattr(mod, "trimmed", lambda *a: 0)
    with pytest.raises(SystemExit, match="8.00 s hole"):
        mod.autotrim(ctx, WHY)
    assert ctx.calls["run"] == []


def test_a_trim_earns_exactly_one_rerun_and_the_judges_signature(tmp_path, monkeypatch):
    ctx = ctx_of(tmp_path)
    signed = {}
    monkeypatch.setattr(mod, "placed_of", lambda *a: {"lines": []})
    monkeypatch.setattr(mod, "trimmed", lambda *a: 2)
    monkeypatch.setattr(mod.speech_gap, "refusal", lambda placed: None)
    monkeypatch.setattr("studio.plan_verdict.sign",
                        lambda plan, note, **kw: signed.update(note=note, **kw))
    mod.autotrim(ctx, WHY)
    assert ctx.calls["run"] == ["scripts/episode/respot.py", "scripts/episode/timeline.py"]
    assert ctx.calls["battery"] == ["scripts/episode/plan_check.py"]
    assert signed["signed_by"] == "judge:plan@1"               # the judge, never the owner
    assert "2 holds shaved" in signed["note"]


def test_a_still_refused_rerun_raises_the_measured_refusal(tmp_path, monkeypatch):
    ctx = ctx_of(tmp_path)
    monkeypatch.setattr(mod, "placed_of", lambda *a: {"lines": []})
    monkeypatch.setattr(mod, "trimmed", lambda *a: 1)
    monkeypatch.setattr(mod.speech_gap, "refusal", lambda placed: "REFUSED: still 6.4 s")
    monkeypatch.setattr("studio.plan_verdict.sign",
                        lambda *a, **kw: pytest.fail("a refused timeline was signed"))
    with pytest.raises(SystemExit, match="still 6.4 s"):
        mod.autotrim(ctx, WHY)
    assert ctx.calls["run"] == ["scripts/episode/respot.py", "scripts/episode/timeline.py"]


def test_a_refused_battery_is_never_signed(tmp_path, monkeypatch):
    ctx = ctx_of(tmp_path, battery=(1, "G-HOLE       : 1\n    G-HOLE shots 1-2: x"))
    monkeypatch.setattr(mod, "placed_of", lambda *a: {"lines": []})
    monkeypatch.setattr(mod, "trimmed", lambda *a: 1)
    monkeypatch.setattr(mod.speech_gap, "refusal", lambda placed: None)
    monkeypatch.setattr("studio.plan_verdict.sign",
                        lambda *a, **kw: pytest.fail("a refused battery was signed"))
    with pytest.raises(SystemExit, match="battery"):
        mod.autotrim(ctx, WHY)


def test_the_signer_is_the_plan_judge():
    assert mod.judge_signer() == "judge:plan@1"


def test_trimmed_writes_the_shaved_plan_through_the_contract(tmp_path):
    from studio import episode_home
    from studio import plan_cures as pc
    from studio.episode_spec import Episode
    ctx = ctx_of(tmp_path)
    doc = episode_with_wordless_run().model_dump()
    (ctx.home / "plan.json").write_text(json.dumps(doc), encoding="utf-8")
    placed = pc._projection(doc, 3.0)                          # the 9+ s hole, measured-like
    n = mod.trimmed(ctx, placed)
    assert n > 0
    after = episode_home.read_json(ctx.home / "plan.json")
    assert after != doc
    Episode.model_validate(after)
