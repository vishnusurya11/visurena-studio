"""A2, honest prompt provenance (craft ruling 2026-10-21, wave 0).

`take_inputs.Inputs.reworded` was declared and read but never set, so QC printed "inputs: all 28
takes current" on Jekyll ep01 while 27 of the 28 kept takes had rendered from other words than the
cards on disk, 8 of them night takes lit by a sun.  `check` now sets `reworded` from the take's own
graph; `stale_words` re-lints a recorded prompt under today's HARD rules.  Both are REPORT rows:
`current` (the pictures wall) does not move, and nothing re-renders (advisory under freeze).
Fixtures: Jekyll ep01's 28 graphs, shots.json, prompts.json and plan.json, copied by name into
tests/fixtures/craft/episodes/ep01.  No render, no network, no spend."""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from scripts.episode import qc
from studio import take_currency as tc, take_inputs as ti

BOOK = Path(__file__).parent / "fixtures" / "craft"
TAKES = BOOK / "episodes" / "ep01" / "takes" / "r2v"


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def records() -> list[dict]:
    return read(TAKES / "shots.json")


def night() -> dict[int, bool]:
    plan = read(BOOK / "episodes" / "ep01" / "plan.json")
    return {int(r["index"]): ti.night_of(plan["setups"][r["setup"]]) for r in records()}


def fake_take(tmp_path: Path, said: str) -> Path:
    take = tmp_path / "T00.mp4"
    tc.graph_of(take).write_text(json.dumps({"1": {"class_type": tc.RENDER_NODE, "inputs": {"prompt": said}}}),
                                 encoding="utf-8")
    return take


# ---- reworded is set, and moves nothing else ----------------------------------------------------

def test_check_sets_reworded_when_the_recorded_words_are_not_the_cards(tmp_path):
    take = fake_take(tmp_path, "the girl crosses")
    assert ti.check(take, [], built="the girl runs").reworded is True
    assert ti.check(take, [], built="  the girl crosses\n").reworded is False


def test_check_without_the_cards_words_claims_nothing(tmp_path):
    assert ti.check(fake_take(tmp_path, "the girl crosses"), []).reworded is False


def test_reworded_never_moves_the_pictures_verdict(tmp_path):
    take = fake_take(tmp_path, "the girl crosses")
    assert ti.check(take, [], built="other").current == ti.check(take, []).current


def test_the_cards_words_are_read_from_prompts_json():
    built = ti.built_prompts(TAKES)
    assert len(built) == 28 and built[13].startswith("subject_definitions:")
    assert ti.built_prompts(BOOK) is None          # not measured, never an empty build


# ---- stale words: the recorded prompt under today's HARD rules -------------------------------------

def test_recorded_facts_come_off_the_recorded_words():
    said = tc.recorded_prompt(TAKES / "T19.mp4")
    facts = ti.recorded_facts(said, night=False, frames=130)
    assert facts["night"] is False and facts["frames"] == 130
    assert "dove-grey top hat" in facts["cast_rows"]
    assert facts["lines"] == [{"text": "I want to ask the name of that man who walked over the child."}]


def test_a_night_take_with_a_sun_fails_a_current_hard_rule():
    assert any(f.startswith("L28") for f in ti.stale_words(TAKES / "T06.mp4", night=True, frames=200))


def test_a_spoken_walk_is_not_a_walk_with_no_pace():
    frames = int(records()[19]["frames"])
    assert ti.stale_words(TAKES / "T19.mp4", night=False, frames=frames) == []


def test_a_take_with_no_graph_is_not_measured(tmp_path):
    assert ti.stale_words(tmp_path / "T00.mp4") is None


# ---- the QC line: the ruling's numbers on ep01 -----------------------------------------------------

def ep01_audited() -> dict[int, ti.Inputs]:
    built = ti.built_prompts(TAKES)
    return {int(r["index"]): ti.check(BOOK / r["rel_path"], [], built.get(int(r["index"]))) for r in records()}


def test_ep01_has_27_takes_from_older_words_and_9_failing_a_current_hard_rule():
    """8 night takes lit by a sun (L28), and T01's rendered "in profile,, feet" since craft ruling A18
    widened L19 to the doubled comma."""
    block = ti.words(ep01_audited(), records(), BOOK, night())
    assert len(block["reworded"]) == 27 and block["reworded"][0] == "T00" and "T01" not in block["reworded"]
    assert sorted(block["fail"]) == ["T00", "T01", "T06", "T07", "T08", "T09", "T10", "T11", "T12"]
    assert block["line"] == ("words: 27 of 28 rendered from older words; 9 of 28 fail a current HARD rule, at "
                             "least (L7 L9 L10 L11 L12 L16 L17 unread) (advisory under freeze)")


def test_the_qc_block_carries_the_words_and_the_wall_does_not_read_them():
    i = SimpleNamespace(take_dir=TAKES, records=records(), book=BOOK,
                        episode=SimpleNamespace(setups={k: SimpleNamespace(**v) for k, v in
                                                        read(BOOK / "episodes" / "ep01" / "plan.json")["setups"].items()}))
    report = {"inputs": {"ok": True, "line": "inputs: all 28 takes current"}}
    out = qc.words_rows(i, report, audited=ep01_audited())
    assert out["inputs"]["words"]["line"].startswith("words: 27 of 28 rendered from older words; 9 of 28 fail")
    assert qc.inputs_ok(out) is True
