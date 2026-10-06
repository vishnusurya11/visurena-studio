"""G-CURE-VERIFY: an llm rewrite reaches a plan field, a refs row or a props
card ONLY when the lint family that ordered it re-passes in code and no banned
word rode in; one re-ask carrying the verifier's complaint, then the row stays
uncured.  The gateway is stubbed at studio.llm's `_agent` seam -- no test may
call a paid API -- and the whole pass is capped at MAX_LLM_CURES and skipped
outright by --no-llm."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

from strands.types.exceptions import StructuredOutputException

from studio import llm, plan_cures as pc

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("plan_repair", ROOT / "scripts" / "episode" / "plan_repair.py")
pr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pr)

ROW = "G-TAKELINT shot 3: L2 STILLNESS: ['held'] [plan]"
GOOD = "His hand rests at the brim, fingers curled over it."
BAD = "His hand is held at the brim."


def doc_of() -> dict:
    return {"shots": [{"index": 3, "setup": "bar", "frame": "A man at the bar.",
                       "at_rest": "His hand held at the brim.", "motion": "", "end": ""}],
            "setups": {"bar": {"described": "A low taproom."}}}


def agent_of(answers: list):
    """A canned structured caller: each answer is a text or an exception."""
    calls = []

    def call(prompt, structured_output_model=None):
        calls.append(prompt)
        said = answers[min(len(calls), len(answers)) - 1]
        if isinstance(said, Exception):
            raise said
        return SimpleNamespace(structured_output=pc.RewrittenField(text=said))

    call.calls = calls
    return call


def test_a_verified_rewrite_lands_in_the_plan_field():
    doc, done = pc.llm_field_cure(None, doc_of(), ROW, _agent=agent_of([GOOD]))
    assert done and doc["shots"][0]["at_rest"] == GOOD


def test_a_rewrite_reintroducing_held_is_reasked_once_then_left_uncured():
    agent = agent_of([BAD, BAD])
    doc, done = pc.llm_field_cure(None, doc_of(), ROW, _agent=agent)
    assert not done
    assert doc["shots"][0]["at_rest"] == "His hand held at the brim."
    assert len(agent.calls) == 2
    assert llm.REFUSED in agent.calls[1]          # the complaint rides the re-ask
    assert "L2" in agent.calls[1]


def test_a_structured_output_exception_is_retried_inside_the_gateway():
    agent = agent_of([StructuredOutputException("bad shape"),
                      StructuredOutputException("bad shape"), GOOD])
    doc, done = pc.llm_field_cure(None, doc_of(), ROW, _agent=agent)
    assert done and len(agent.calls) == 3


def test_a_row_layer_rewrite_lands_in_refs_json(tmp_path):
    book = tmp_path / "book"
    (book / "refs").mkdir(parents=True)
    (book / "refs" / "refs.json").write_text(json.dumps(
        {"refs": [{"entity_id": "mrs_hall", "kind": "character",
                   "physical": "A revolver held at her lap."}]}), encoding="utf-8")
    row = "G-ROWTEXT L2 STILLNESS: ['held'] [row mrs_hall]"
    _, done = pc.llm_field_cure(book, {}, row, _agent=agent_of(
        ["A revolver resting at her lap."]))
    assert done
    said = json.loads((book / "refs" / "refs.json").read_text(encoding="utf-8"))
    assert said["refs"][0]["physical"] == "A revolver resting at her lap."


def test_the_cap_stops_the_twenty_fifth_call(tmp_path, monkeypatch):
    book = tmp_path / "book"
    home = book / "episodes" / "ep03"
    home.mkdir(parents=True)
    (home / "plan.json").write_text("{}", encoding="utf-8")
    asked = []
    monkeypatch.setattr(pc, "llm_field_cure",
                        lambda b, d, r, **kw: (asked.append(r) or (d, False)))
    rows = [f"G-TAKELINT shot {k}: L22 ABSENT MOUTH [shot {k}]: X's mouth [plan]"
            for k in range(25)]
    assert pr.llm_cure_round(book, 3, rows) is False
    assert len(asked) == pc.MAX_LLM_CURES == 24


def test_no_llm_skips_the_pass_entirely(tmp_path, monkeypatch):
    book = tmp_path / "book"
    home = book / "episodes" / "ep03"
    home.mkdir(parents=True)
    (home / "plan.json").write_text("{}", encoding="utf-8")
    rows = ["G-COVER plan: the plan stops at paragraph 40 of 69"]
    from contextlib import nullcontext
    monkeypatch.setattr(pr.episode_home, "book_dir", lambda _: book)
    monkeypatch.setattr(pr, "battery_rows", lambda b, n: (False, rows))
    monkeypatch.setattr(pr, "apply", lambda doc, r, b, n, rate=3.0, llm=True: (doc, list(r), []))
    monkeypatch.setattr(pr, "spend_guard", lambda b, n: nullcontext())
    monkeypatch.setattr(pr, "rewrite_round", lambda b, p, r: False)
    monkeypatch.setattr(pr, "fill_holes", lambda b, n: False)
    monkeypatch.setattr(pr, "Episode", lambda **kw: None)
    monkeypatch.setattr(pr.episode_home, "write_plan", lambda p, d: p)
    monkeypatch.setattr("studio.plan_gates.series_rate", lambda b, n: 3.0, raising=False)
    ran = []
    monkeypatch.setattr(pr, "llm_cure_round", lambda b, n, r: ran.append(1) or False)
    assert pr.main("whatever", 3, no_llm=True) == 1
    assert ran == []
    assert pr.main("whatever", 3, no_llm=False) == 1
    assert ran == [1]
