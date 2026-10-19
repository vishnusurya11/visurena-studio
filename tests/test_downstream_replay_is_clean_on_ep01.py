"""downstream_replay: the steps AFTER the plan sign, replayed read-only and free on a
signed plan.json (Jekyll Kawajiri ep01: three parks for code-ruler faults, 10 min --
step 05's packer read the legacy 8 s budget on a grammar plan (5d3dc08), step 06's
lint read the references band before any panel existed (5c23230)).

Three checks: step_05 `packed()` is [], `plan_cures.holds` on a deep copy moves no shot's
seconds past the hand's tolerance, and the takes_r2v prompt lint runs dry."""
import json
import re
import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, "scripts/episode")
import downstream_replay as dr

FIX = Path(__file__).parent / "fixtures" / "ep01_replay" / "P02"
STEP05 = Path("scripts/episode/step_05_timeline.py")


def voice() -> dict:
    rows = json.loads((FIX / "lines.json").read_text(encoding="utf-8"))
    rows = rows["lines"] if isinstance(rows, dict) else rows
    return {str(r["text"]).strip(): float(r["seconds"]) for r in rows if r.get("seconds") and r.get("passed", True)}


def test_ep01_is_clean_on_master():
    assert dr.replay(FIX / "plan.json", voice=voice(), lint=lambda doc, rate: []) == []


def test_a_grammar_plan_packs_nothing_on_the_measured_view():
    assert dr.packed_runs(json.loads((FIX / "plan.json").read_text(encoding="utf-8")), 2.45, voice()) == []


def test_the_prompt_lint_runs_dry_and_its_rows_are_ruler_rows():
    rows = dr.replay(FIX / "plan.json", voice=voice(), lint=lambda doc, rate: ["G-TAKELINT shot 5: P8 x"])
    assert rows == ["RULER prompt lint: G-TAKELINT shot 5: P8 x"]


def test_a_missing_lint_is_skipped_not_a_fault():
    assert dr.replay(FIX / "plan.json", voice=voice()) == []


def test_reverting_the_5d3dc08_guard_in_a_temp_copy_reports_a_ruler_fault(tmp_path):
    src = STEP05.read_text(encoding="utf-8")
    assert "tk.budget_for(SimpleNamespace(grammar=plan.get(\"grammar\") or \"\"))" in src
    old = re.sub(r"budget = tk\.budget_for\(SimpleNamespace\([^\n]*\n", "budget = tk.BUDGET\n", src)
    assert old != src
    copy = tmp_path / "step_05_old.py"
    copy.write_text(old.replace("sys.path.insert(0, str(Path(__file__).resolve().parents[2]))",
                                f"sys.path.insert(0, {str(Path.cwd())!r})"), encoding="utf-8")
    sys.path.insert(0, str(tmp_path))
    try:
        import step_05_old
        rows = dr.replay(FIX / "plan.json", voice=voice(), step05=step_05_old, lint=lambda doc, rate: [])
    finally:
        sys.path.remove(str(tmp_path))
    assert rows and rows[0].startswith("RULER step 05 packs")


def test_holds_that_moves_a_shot_past_the_tolerance_is_a_ruler_fault():
    doc = json.loads((FIX / "plan.json").read_text(encoding="utf-8"))
    doc["shots"][27].update(coda_s=4.0, beat_s=1.5)     # past the take: the cure would shave it back
    rows = dr.replay(doc, voice=voice(), lint=lambda d, r: [])
    assert rows and rows[0].startswith("RULER holds would move shot 27")


def test_the_replay_writes_nothing_beside_the_plan(tmp_path):
    shutil.copy(FIX / "plan.json", tmp_path / "plan.json")
    dr.replay(tmp_path / "plan.json", voice=voice(), lint=lambda doc, rate: [])
    assert sorted(p.name for p in tmp_path.iterdir()) == ["plan.json"]
