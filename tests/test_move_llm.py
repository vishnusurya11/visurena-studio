"""The LLM escape for camera heads no mechanical candidate cures (AREA 2):
one targeted workhorse structured call per unfixed shot, guard_spend-walled,
with a strict pydantic head contract and the SAME `head_ok` replay on every
answer -- one re-ask, then the row stays uncured for the writer.  Every test
injects a fake through `studio.llm`'s `_agent` seam: NO paid API, ever."""
from __future__ import annotations

import pytest
from strands.types.exceptions import StructuredOutputException
from types import SimpleNamespace

from studio import llm, move_llm, move_rebalance as mr

AT_REST = "THE FOCUS OF THE PICTURE IS the lamp; the gate stands at the LEFT"


def shot_of(**over) -> dict:
    base = {"index": 5, "setup": "yard", "size": "medium", "frame": "The yard.",
            "at_rest": AT_REST, "camera": "", "faces": [], "extras": 0,
            "motion": "The camera holds a locked-off frame; his hand lifts"}
    base.update(over)
    return base


class FakeCaller:
    """The `_agent` seam: canned answers (or exceptions), never a network client."""

    def __init__(self, answers):
        self.answers, self.calls = list(answers), []

    def __call__(self, prompt, structured_output_model=None):
        self.calls.append(prompt)
        got = self.answers[min(len(self.calls), len(self.answers)) - 1]
        if isinstance(got, Exception):
            raise got
        return SimpleNamespace(structured_output={"head": got})


GOOD = "The camera pushes in slowly toward the gate, travelling a forearm, across the whole shot"
BAD_AIM = "The camera pans from the heliograph to the gate, travelling a forearm, across the whole shot"


def test_fallback_uses_workhorse_and_the_seam(monkeypatch):
    seen, real = {}, llm.structured

    def spy(tier, prompt, schema, **kw):
        seen["tier"] = tier
        return real(tier, prompt, schema, **kw)

    monkeypatch.setattr(llm, "structured", spy)
    fake = FakeCaller([GOOD])
    got = move_llm.fallback_head(shot_of(), {}, {}, "locked", "pan_to", caller=fake)
    assert got == GOOD and seen["tier"] == "workhorse"
    assert len(fake.calls) == 1
    prompt = fake.calls[0]
    assert AT_REST in prompt                              # the cell is quoted
    assert "tilt_down" in prompt and "rack_focus" in prompt   # the banned ids
    assert "locked" in prompt and "pan_to" in prompt          # the neighbours
    assert "travelling" in prompt and "across the whole shot" in prompt


@pytest.mark.parametrize("bad", [
    "Camera pushes in toward the gate across the whole shot",      # no "The camera "
    "The camera pushes in toward the gate; he turns",              # a semicolon
    "The camera pushes in very slowly and very carefully toward the small gate "
    "at the far left of the picture while the light falls and the dust rises and "
    "settles again across the whole shot",                          # over 30 words
    "The camera pushes in slowly toward the gate",                  # no whole-shot tail
])
def test_contract_refuses_a_bad_head(bad):
    fake = FakeCaller([bad])
    with pytest.raises(StructuredOutputException):
        llm.structured("workhorse", "p", move_llm.MotionHead, retries=3, _agent=fake)
    assert len(fake.calls) == 3          # every retry consumed re-asking


def test_head_failing_head_ok_gets_one_reask_then_uncured():
    fake = FakeCaller([BAD_AIM])         # G-AIM-violating, twice
    got = move_llm.fallback_head(shot_of(), {}, {}, "", "", caller=fake)
    assert got is None and len(fake.calls) == 2
    assert llm.REFUSED in fake.calls[1] and "G-AIM" in fake.calls[1]
    doc = {"shots": [shot_of()], "lines": [], "setups": {"yard": {"crowd": ""}}}
    doc, still = move_llm.cure_unfixed(doc, [5], doc["setups"], caller=FakeCaller([BAD_AIM]))
    assert still == [5]
    assert doc["shots"][0]["motion"].startswith("The camera holds a locked-off frame")


def test_a_verified_answer_is_spliced_and_the_actions_survive():
    doc = {"shots": [shot_of(motion="his hand lifts the lid; steam rises")],
           "lines": [], "setups": {"yard": {"crowd": ""}}}
    doc, still = move_llm.cure_unfixed(doc, [5], doc["setups"], caller=FakeCaller([GOOD]))
    assert still == []
    got = doc["shots"][0]["motion"]
    assert got.startswith(GOOD) and "his hand lifts the lid" in got and "steam rises" in got


def test_plan_repair_routes_unfixed_shots_to_the_llm_and_keeps_their_rows(monkeypatch):
    """LLM-ESCAPE wiring: the rebalance branch hands its `unfixed` shots to
    `move_llm.cure_unfixed`, and a shot still unfixed leaves its own fault row
    in `uncured` -- the writer path, exactly as today."""
    import importlib.util
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location(
        "pr_moves", root / "scripts" / "episode" / "plan_repair.py")
    pr = importlib.util.module_from_spec(spec)
    sys.modules["pr_moves"] = pr
    spec.loader.exec_module(pr)
    seen = {}
    monkeypatch.setattr(pr.pc, "rebalance_heads",
                        lambda doc, idx: (seen.setdefault("idx", idx), (doc, [5]))[1])
    monkeypatch.setattr(move_llm, "cure_unfixed",
                        lambda doc, unfixed, setups, caller=None:
                        (seen.setdefault("unfixed", unfixed), (doc, [5]))[1])
    rows = ["G-MOVES plan: distinct catalog moves over 23 shots, measured 6 against 8",
            "M2 shot 5: the head names no camera move. Open with one, before the first semicolon"]
    _, uncured, _ = pr.apply({"shots": [], "lines": [], "setups": {}}, rows, root / "nowhere")
    assert seen["idx"] == [5] and seen["unfixed"] == [5]
    assert uncured == [rows[1]]          # the plan-level row re-measures next round


def test_overbudget_and_contentfiltered_leave_the_row_uncured():
    for exc in (llm.OverBudget("the ceiling"), llm.ContentFiltered("refused")):
        fake = FakeCaller([exc])
        assert move_llm.fallback_head(shot_of(), {}, {}, "", "", caller=fake) is None
        assert len(fake.calls) == 1      # no retry: the row goes to the writer
