"""The grammar replay reads every plan by name, judges it at its own voice, and
reports a plan the contract no longer reads instead of crashing.  $0."""
from __future__ import annotations

import json
from pathlib import Path

from scripts.episode import grammar_replay as gr
from tests.test_episode_writer import canned_plan


def _book(tmp_path: Path) -> Path:
    for n, doc in ((1, canned_plan(1)), (2, {"number": 2})):
        home = tmp_path / "episodes" / f"ep{n:02d}"
        home.mkdir(parents=True)
        (home / "plan.json").write_text(json.dumps(doc), encoding="utf-8")
    return tmp_path


def test_every_plan_is_found_in_episode_order(tmp_path):
    book = _book(tmp_path)
    assert [p.parent.name for p in gr.plan_paths(book)] == ["ep01", "ep02"]


def test_a_plan_is_replayed_and_a_broken_one_reported(tmp_path):
    book = _book(tmp_path)
    good, bad = (gr.replay(book, p) for p in gr.plan_paths(book))
    assert good["shots"] == 24 and good["pushes"] == 24 and good["faults"]["G-ACT"] == 1
    assert bad["refused_by_contract"] is True


def test_gate_counts_read_the_gate_name():
    assert gr.gate_counts(["G-WIDE shot 0: x", "G-WIDE plan: y", "G-MA plan: z"]) == {"G-WIDE": 2, "G-MA": 1}
