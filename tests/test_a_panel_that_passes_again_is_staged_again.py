"""A shot leaves refs_only.json when its panel passes both panel checks again (Jekyll ep06 retro D+E, 2026-10-29).

Panels 24/25 drew Utterson twice; the panel ladder put both shots on refs_only.json, so their takes staged the
cast sheets and the place picture and no panel -- H3 opened on the empty street and cut to the doorstep (T24's
hard cut, T25's crash zoom).  The panels were redrawn and passed, but nothing ever took a shot off the list, so
the takes kept rendering without them.  Off the list, the take's build stages the panel again and take currency
reads the panel-less take as stale (a picture it did not stage), so it re-renders from the panel."""
from __future__ import annotations

import json

from studio import refs_only


def board(tmp_path, content, dq):
    room = tmp_path / "storyboard"
    room.mkdir()
    (room / "panel_content.json").write_text(json.dumps([{"shot": s, "passed": p} for s, p in content.items()]))
    (room / "panel_dq.json").write_text(json.dumps([{"shot": s, "passed": p} for s, p in dq.items()]))
    refs_only.add(tmp_path, [24, 25, 16], "a duplicated or extra person after the climb: the panel is not staged")
    return tmp_path


def test_a_shot_whose_panel_passes_both_checks_is_lifted(tmp_path):
    home = board(tmp_path, {24: True, 25: True, 16: False}, {24: True, 25: True, 16: True})
    assert refs_only.lift_passing(home) == [24, 25]
    assert refs_only.read(home) == {16}


def test_a_panel_that_fails_either_check_stays_off_the_board(tmp_path):
    home = board(tmp_path, {24: True, 25: False, 16: True}, {24: False, 25: True, 16: True})
    assert refs_only.lift_passing(home) == [16]
    assert refs_only.read(home) == {24, 25}


def test_a_lift_is_recorded_beside_the_reason_it_was_added(tmp_path):
    home = board(tmp_path, {24: True, 25: True, 16: True}, {24: True, 25: True, 16: True})
    refs_only.lift_passing(home)
    doc = json.loads((home / refs_only.FILE).read_text(encoding="utf-8"))
    assert doc["shots"] == [] and set(doc["lifted"]) == {"16", "24", "25"}
    assert "passed both panel checks" in doc["lifted"]["24"]


def test_no_verdicts_lift_nothing(tmp_path):
    refs_only.add(tmp_path, [3], "seam")
    assert refs_only.lift_passing(tmp_path) == [] and refs_only.read(tmp_path) == {3}


def test_step_08_lifts_after_the_ladder(monkeypatch, tmp_path):
    from scripts.episode import step_08_panels as s08
    calls = []
    monkeypatch.setattr(s08, "rebuild", lambda ctx, only=None: calls.append("rebuild"))
    monkeypatch.setattr(s08.judged_gate, "clear", lambda *a, **k: calls.append("clear"))
    monkeypatch.setattr(s08.gate_policy, "of", lambda stage, gate: type("P", (), {"max_grids": 0})())
    monkeypatch.setattr(s08.panel_ladder, "climb", lambda ctx, rebuild, cap: type("C", (), {"rungs": None, "keep_best": None})())
    monkeypatch.setattr(s08, "judge_of", lambda ctx: None)
    monkeypatch.setattr(refs_only, "lift_passing", lambda home: calls.append("lift") or [24])

    class Ctx:
        home, stage = tmp_path, "episode"

        def open_step(self, step):
            pass

        def log(self, *a, **k):
            calls.append("log")
    s08.run(Ctx())
    assert calls[:3] == ["rebuild", "clear", "lift"]
