"""QC names the cross-stage pair it used to mute: take HARD rows the grammar demoted beside the plan's hold cures
(craft ruling A26).

A frozen-whole row on a take the plan's grammar locked is demoted to an advisory ("locked on the grammar"), and the
plan's own `hold_extra_pushes` cure is what locks those shots: one stage writes the hold the next stage would
refuse.  Nothing reported the pair.  QC now prints both counts in one line, report only (whether holds should move
is the shot-framework panel's question).  Fixture: ep01's take gate notes that carry the demotion
(tests/fixtures/craft/episodes/ep01/takes/r2v/grammar_demoted.json, 8 rows on disk 2026-10-21; the ruling's 9 was
counted before a retake) and ep01's plan.cures.jsonl (6 of 17 cure rounds ran hold_extra_pushes)."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from scripts.episode import qc
from studio.judges import registry

EP01 = Path(__file__).parent / "fixtures" / "craft" / "episodes" / "ep01"


def episode(tmp_path) -> Path:
    home = tmp_path / "ep01"
    room = home / "takes" / "r2v"
    room.mkdir(parents=True)
    shutil.copy(EP01 / "plan.cures.jsonl", home / "plan.cures.jsonl")
    notes = json.loads((EP01 / "takes" / "r2v" / "grammar_demoted.json").read_text(encoding="utf-8"))["notes"]
    for take, said in notes.items():
        gates = [{"name": "frozen-whole", "hard": False, "ok": False, "note": n} for n in said]
        (room / f"{take}.dq.json").write_text(json.dumps({"gates": gates + [{"name": "foreign", "note": "0"}]}),
                                              encoding="utf-8")
    (room / "T99.dq.json").write_text(json.dumps({"gates": [{"name": "frozen-whole", "note": "84% static"}]}),
                                      encoding="utf-8")
    return home


def test_ep01_prints_the_demoted_rows_beside_the_hold_cures(tmp_path):
    home = episode(tmp_path)
    block = qc.cross_stage(home / "takes" / "r2v", home)
    assert (block["demoted"], block["holds"]) == (8, 6)
    assert block["line"].startswith("cross-stage: 8 take HARD rows demoted (locked on the grammar); "
                                    "6 hold_extra_pushes plan cures")


def test_an_episode_with_neither_says_zero(tmp_path):
    block = qc.cross_stage(tmp_path / "none", tmp_path)
    assert (block["demoted"], block["holds"]) == (0, 0)


def test_the_pair_is_named_in_the_judges_registry():
    assert registry.CROSS_STAGE["frozen-whole"] == "hold_extra_pushes"


def test_the_row_never_fails_qc(tmp_path, monkeypatch):
    monkeypatch.setattr(qc, "cross_stage", lambda *a: 1 / 0)
    from types import SimpleNamespace
    report = qc.cross_stage_rows(SimpleNamespace(take_dir=tmp_path, book=tmp_path, number=1), {})
    assert report["inputs"]["cross_stage"]["line"].startswith("cross-stage: not measured")
