"""G5 in qc.py: the edit-integrity verdict and the two roll-ups that put the take
gate and the sheet gate on the master's own report.  Pure JSON in, no master
decoded, nothing spends.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("ep_qc_rollup", ROOT / "scripts" / "episode" / "qc.py")
qc = importlib.util.module_from_spec(spec)
sys.modules["ep_qc_rollup"] = qc
spec.loader.exec_module(qc)

GOOD = {"lufs_ok": True, "tp_ok": True, "missing_cuts": [], "lines": [{"passed": True}],
        "edit": {"ok": True, "measured": True}}
"""The edit block carries `measured` now.  An ABSENT or UNMEASURED block is no
longer a pass: `.get("edit", {}).get("ok", True)` made a missing measurement
clean twice over, and G5.6 provenance was returning `measured: False` on every
episode ever cut because nothing wrote its input."""


def write(path: Path, data) -> None:
    path.write_text(json.dumps(data), encoding="utf-8")


def test_the_verdict_fails_when_the_edit_is_not_the_takes():
    """master_iter11: T22's frames 133-136 were another picture (the card started 4
    frames early), and the picture began 0.041 s late."""
    assert qc.verdict(GOOD)
    assert not qc.verdict({**GOOD, "edit": {"ok": False, "measured": True}})
    # AND AN EDIT GATE THAT DID NOT RUN IS NOT A PASS
    assert not qc.verdict({k: v for k, v in GOOD.items() if k != "edit"})
    assert not qc.verdict({**GOOD, "edit": {"ok": True, "measured": False}})


def test_a_spent_retake_budget_is_printed_red_and_does_not_fail_the_master():
    """The cut still needs a picture, so the worst take on disk is still the take;
    it is named in the report and in the iteration log instead."""
    report = {**GOOD, "takes": {"pass": 9, "of": 19, "fail": ["T01"], "budget_spent": ["T01"]}}
    assert qc.verdict(report)


def test_the_takes_rollup_counts_passes_and_names_the_failures(tmp_path):
    write(tmp_path / "shots.json", [{"index": 0}, {"index": 1}, {"index": 2}])
    write(tmp_path / "T00.dq.json", {"passed": True, "score": 100.0})
    write(tmp_path / "T01.dq.json", {"passed": False, "score": 47.5, "budget_spent": True})
    write(tmp_path / "T02.dq.json", {"passed": False, "score": 70.0, "budget_spent": False})
    for n in range(3):
        write(tmp_path / f"T{n:02d}.content.json", {"passed": True})
    roll = qc.takes_rollup(tmp_path)
    assert roll["pass"] == 1 and roll["of"] == 3
    assert roll["fail"] == ["T01", "T02"] and roll["budget_spent"] == ["T01"]
    assert roll["worst"] == ("T01", 47.5)


def test_the_takes_rollup_names_what_it_could_not_judge(tmp_path):
    # An empty rollup used to read as clean. With no record of which takes
    # exist, it now says so, and the QC verdict fails on it (audit item 6).
    roll = qc.takes_rollup(tmp_path)
    assert roll["of"] == 0 and roll["unjudged"]


def test_sheet_spend_is_read_from_the_books_own_ledger(tmp_path):
    rows = [{"purpose": "storyboard seq_gateway_0", "usd_estimate": 0.2},
            {"purpose": "storyboard seq_gateway_0 STRICT", "usd_estimate": 0.2},
            {"purpose": "storyboard seq_lab_0", "usd_estimate": 0.2},
            {"purpose": "character sheet holmes", "usd_estimate": 0.08}]
    (tmp_path / "spend.jsonl").write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    assert qc.sheet_spend(tmp_path) == {"gateway": 0.4, "lab": 0.2}
    assert qc.sheet_spend(tmp_path / "nowhere") == {}


def test_the_sheet_rollup_names_the_setup_its_strict_draws_and_what_it_cost(tmp_path):
    frames = tmp_path / "frames"
    (frames / "plates").mkdir(parents=True)
    (frames / "cells").mkdir(parents=True)
    (frames / "sheets").mkdir(parents=True)
    write(frames / "sheets" / "seq_gateway.dq.json", {"setup": "gateway", "passed": False, "sheets": [
        {"sheet": "seq_gateway_0.png", "strict": False, "duplicates": [["Q07_0", "Q07_0E"]]},
        {"sheet": "seq_gateway_0.png", "strict": True, "duplicates": []}]})
    write(frames / "sheets" / "seq_lab.dq.json", {"setup": "lab", "passed": True, "sheets": [
        {"sheet": "seq_lab_0.png", "strict": False, "duplicates": []}]})
    (tmp_path / "spend.jsonl").write_text(json.dumps(
        {"purpose": "storyboard seq_gateway_0", "usd_estimate": 0.2}), encoding="utf-8")
    rows = qc.sheets_rollup(frames, tmp_path)
    assert [r["setup"] for r in rows] == ["gateway", "lab"]
    assert rows[0] == {"setup": "gateway", "passed": False, "sheets": 2, "strict_draws": 1,
                       "duplicate_pairs": [["Q07_0", "Q07_0E"]], "usd": 0.2}
    assert rows[1]["usd"] == 0.0 and rows[1]["passed"] is True


def test_a_failing_sheet_does_not_fail_the_master_either():
    """G3 owns the sheet; by the time a master exists the money is long spent.  The
    roll-up is printed so the iteration log names it, not so the cut is rejected."""
    report = {**GOOD, "sheets": [{"setup": "gateway", "passed": False, "usd": 0.4}]}
    assert qc.verdict(report)
