"""`rehearse.py smoke` with no sandbox says where smoke runs (2026-10-21_ep02_proof DESIGN 3).

smoke stands on a FIXTURE sandbox (tests/fixtures/proof/scenarios/smoke staged over the tiny stand-in
book) that only tests/test_proof_scenario_smoke.py builds.  From the CLI it fell through to the S0a
checkpoint lookup and the first real window (2026-10-21 17:43 PDT) wrote "checkpoint after_12
absent: run `rehearse.py checkpoints` (S0a) first" -- advice that can never come true: smoke is ep02
and S0a only ever makes ep01 checkpoints.  The CLI now names the test that runs it."""
from __future__ import annotations

import json

from scripts.proof import rehearse


def test_smoke_from_the_cli_names_the_test_that_runs_it(tmp_path, monkeypatch):
    monkeypatch.setattr(rehearse, "refuse_if_live", lambda: None)
    out = rehearse.run_scenario("smoke", results=tmp_path / "results")
    doc = json.loads((tmp_path / "results" / "smoke.json").read_text(encoding="utf-8"))
    assert out["blocked"] and "tests/test_proof_scenario_smoke.py" in out["blocked"][0]
    assert "checkpoints" not in out["blocked"][0] and doc["rows"][0]["passed"] is False


def test_a_checkpoint_scenario_still_asks_for_the_checkpoints_run(tmp_path, monkeypatch):
    monkeypatch.setattr(rehearse, "refuse_if_live", lambda: None)
    monkeypatch.setattr(rehearse, "missing_packages", lambda sid: [])
    monkeypatch.setattr(rehearse, "checkpoint_box", lambda n, name, base=None: None)
    out = rehearse.run_scenario("F1", results=tmp_path / "results")
    assert out["blocked"] == ["checkpoint after_08 absent: run `rehearse.py checkpoints` (S0a) first"]
