"""`rehearse.py all` runs every scenario but S0a and smoke (2026-10-21_ep02_proof DESIGN 3).

The order is memos, then `checkpoints` (which IS S0a), then `all`.  The first real window's `all`
ran S0a a second time: a second full ep01 replay (hours once the plan signs), a second ckpt sandbox,
and results/S0a.json overwritten by the second run.  `all` leaves S0a to `checkpoints`."""
from __future__ import annotations

from scripts.proof import rehearse


def ran(monkeypatch, argv: list[str]) -> list[str]:
    seen: list[str] = []
    monkeypatch.setattr(rehearse, "run_scenario", lambda sid, *a, **k: seen.append(sid) or {"scenario": sid})
    assert rehearse.main(argv) == 0
    return seen


def test_all_runs_every_scenario_but_s0a_and_smoke(monkeypatch):
    seen = ran(monkeypatch, ["all"])
    assert "S0a" not in seen and "smoke" not in seen
    assert set(seen) == set(rehearse.TABLE) - {"S0a", "smoke"}


def test_checkpoints_runs_s0a_alone(monkeypatch):
    assert ran(monkeypatch, ["checkpoints"]) == ["S0a"]
