"""The panel ladder can climb inside an owner's repair (Jekyll ep06 retro C, 2026-10-29).

Two runs under owner order 62 (redo 08) judged panels 24/25 failing G-WHO and climbed nothing: the rung was
priced at 1900 s (ep13, 2026-09-27, before the content read became incremental) and the repair's reserve for
the steps after 08 left less than that, so `affordable` refused every rung.  Jekyll's measured regrid rounds:
97-458 s (ep01-06).  And the episode's rounds and climbed grids had gone to the Poole sheet redraws hours
earlier, so a fault a new gate finds late had nothing left.  The rung is priced at what a round costs now, and
an owner redo of 08 gives the ladder one fresh round and forgets the grids that climbed before it."""
from __future__ import annotations

import json

from studio import panel_ladder, step_attempts


def test_a_rung_is_priced_at_a_measured_round():
    assert panel_ladder.RUNG_SECONDS == 600.0
    assert all(r.cost_seconds == panel_ladder.RUNG_SECONDS for r in panel_ladder.ladder().rungs)


def test_reopening_refunds_one_round_and_forgets_the_climbed_grids(tmp_path):
    step_attempts.spend(tmp_path, panel_ladder.REGRID, 400.0)
    step_attempts.spend(tmp_path, panel_ladder.REGRID, 500.0)
    panel_ladder.remember_climbed(tmp_path, "ep06_grid_doorstep_poole_1x1_a")
    panel_ladder.reopen(tmp_path, order=62)
    assert step_attempts.count(tmp_path, panel_ladder.REGRID) == 1
    assert panel_ladder.load_climbed(tmp_path) == []
    doc = json.loads((tmp_path / "storyboard" / panel_ladder.LADDER_FILE).read_text(encoding="utf-8"))
    assert doc["reopened"][-1]["order"] == 62 and doc["reopened"][-1]["forgot"] == ["ep06_grid_doorstep_poole_1x1_a"]


def test_an_order_reopens_once(tmp_path):
    step_attempts.spend(tmp_path, panel_ladder.REGRID, 400.0)
    step_attempts.spend(tmp_path, panel_ladder.REGRID, 500.0)
    panel_ladder.reopen(tmp_path, order=62)
    panel_ladder.reopen(tmp_path, order=62)
    assert step_attempts.count(tmp_path, panel_ladder.REGRID) == 1


def test_step_08_reopens_under_an_owner_order_only(monkeypatch, tmp_path):
    from scripts.episode import step_08_panels as s08
    opened = []
    monkeypatch.setattr(panel_ladder, "reopen", lambda home, order: opened.append(order))
    monkeypatch.setattr(s08, "owner_order", lambda ctx: 62)
    s08.reopen_for_owner(type("Ctx", (), {"home": tmp_path, "log": lambda *a, **k: None})())
    monkeypatch.setattr(s08, "owner_order", lambda ctx: None)
    s08.reopen_for_owner(type("Ctx", (), {"home": tmp_path, "log": lambda *a, **k: None})())
    assert opened == [62]
