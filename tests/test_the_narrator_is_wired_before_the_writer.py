"""The book's narrator reaches every place a speaker is chosen or judged
(Jekyll ep01 review, 2026-10-13): the brief names him, the free alias cure
maps the writer's 'the narrator' to him, the battery's G-SPEAKER reads him,
and step 02 stops before any writer is asked when he is unset.  $0."""
from __future__ import annotations

import inspect
from types import SimpleNamespace

import pytest

from agents import episode_writer as ew
from scripts.episode import plan_check, step_02_plan
from studio import book_narrator as bn
from studio import plan_brief, plan_cures

CAST = ["gabriel_john_utterson", "richard_enfield"]


def test_the_brief_carries_the_declared_narrator(tmp_path):
    bn.declare(tmp_path, bn.dedicated("calm, low", "third person"))
    got = plan_brief.narrator_section(tmp_path)
    assert got["speaker"] == "narrator" and got["person"] == "third" and got["on_camera"] is False
    assert "SPEAKS EVERY NARRATION LINE" in got["rule"]
    assert "narrator" in plan_brief.SECTIONS


def test_the_brief_says_nothing_when_no_narrator_is_set(tmp_path):
    assert plan_brief.narrator_section(tmp_path) is None


def test_the_alias_cure_maps_a_narrator_word_to_the_books_narrator():
    doc = {"lines": [{"speaker": "the narrator"}, {"speaker": "richard_enfield"}]}
    out = plan_cures.alias_speakers(doc, CAST, "narrator")
    assert [l["speaker"] for l in out["lines"]] == ["narrator", "richard_enfield"]


def test_the_writer_aliases_to_the_brief_narrator_before_the_contract():
    doc = {"lines": [{"speaker": "Narrator"}], "shots": []}
    brief = {"cast": [{"entity_id": c} for c in CAST], "narrator": {"speaker": "narrator"}}
    assert ew.structural_cures(doc, brief)["lines"][0]["speaker"] == "narrator"


def test_the_battery_speaker_gate_stops_on_an_unset_narrator(tmp_path, capsys):
    ep = SimpleNamespace(lines=[SimpleNamespace(index=0, kind="narration", speaker="narrator", shot=0)])
    assert plan_check.speaker_gate(ep, tmp_path, [{"entity_id": c} for c in CAST]) == 1
    bn.declare(tmp_path, bn.dedicated("calm", "why"))
    assert plan_check.speaker_gate(ep, tmp_path, [{"entity_id": c} for c in CAST]) == 0


def test_step_02_stops_before_the_writer_when_the_narrator_is_unset(tmp_path):
    ctx = SimpleNamespace(book_dir=tmp_path, log=lambda *a, **k: None)
    with pytest.raises(SystemExit, match="NARRATOR"):
        step_02_plan.narrator_or_stop(ctx)
    src = inspect.getsource(step_02_plan.run)
    assert src.index("narrator_or_stop(ctx)") < src.index("desk.resume()")
