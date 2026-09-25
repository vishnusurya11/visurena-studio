"""The episode writer: a brief in, an `Episode` out, through the structured
gateway with a fake caller.  No test here calls a model.

The contract is what is tested -- the skill and the brief reach the prompt, a
refusal is quoted back verbatim, the schema validates, and a caller that
cannot produce the shape surfaces its exception -- never the model's judgement.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest
from strands.types.exceptions import StructuredOutputException

from agents import episode_writer as ew
from studio.episode_spec import Episode

N = 24
NARRATION = "The lead sits at the table and looks at the window while the light comes in."
DIALOGUE = "You came back, then, after all this time, and you brought the cup with you."


def _shot(i: int) -> dict:
    section = "hook" if i == 0 else "turn" if i == 14 else "button" if i == N - 1 else "setup"
    spoken = i in (10, N - 1)
    return {"index": i, "section": section, "setup": "room",
            "size": "close" if spoken else "medium", "faces": ["other"] if spoken else ["lead"],
            "frame": ("Close on the other, face to camera, the window behind."
                      if spoken else "Medium on the lead at the table by the window."),
            "motion": "The camera pushes in across the whole shot; he lifts the cup; the cup rises to his mouth.",
            "camera": "at the table's near end, level with the cup",
            "at_rest": "The cup stands on the table, his hand beside it.",
            "end": "The cup is at his mouth, his elbow up.", "changed": "the cup rises to the mouth",
            "beat_s": 1.0 if i == N - 2 else 0.0}


def _line(i: int) -> dict:
    spoken = i in (10, N - 1)
    return {"index": i, "kind": "dialogue" if spoken else "narration",
            "speaker": "other" if spoken else "lead",
            "text": DIALOGUE if spoken else NARRATION, "shot": i}


def canned_plan(number: int = 3) -> dict:
    """A plan the contract accepts: 24 shots, one line each, the turn at 58 %,
    the button spoken by someone other than the lead, dialogue at 8 %."""
    return {"number": number, "title": "The Yard", "protagonist": "lead", "aspect": "1:1",
            "setups": {"room": {"described": "A plain room with a table and a window",
                                "cast": ["lead", "other"], "landmark": "the window",
                                "geometry": "The window at the far wall, the table before it."}},
            "shots": [_shot(i) for i in range(N)], "lines": [_line(i) for i in range(N)]}


def canned_draft(number: int = 3) -> dict:
    """The same plan in the shape the model returns: setups as a named list,
    beds as typed rows (a provider's strict schema has no dict field)."""
    plan = canned_plan(number)
    plan["setups"] = [{"name": name, **setup} for name, setup in plan["setups"].items()]
    plan["beds"] = [{"from_shot": 0, "tone": "plain"}]
    return plan


class FakeModel:
    """Canned structured output; records every prompt it was given."""

    def __init__(self, *payloads):
        self.payloads, self.prompts = list(payloads), []

    def __call__(self, prompt, structured_output_model=None):
        self.prompts.append(prompt)
        payload = self.payloads.pop(0) if len(self.payloads) > 1 else self.payloads[0]
        if isinstance(payload, Exception):
            raise payload
        return SimpleNamespace(structured_output=payload,
                               metrics=SimpleNamespace(accumulated_usage={
                                   "inputTokens": 10, "outputTokens": 5, "totalTokens": 15}))


BRIEF = {"number": 3, "band": {"min_seconds": 120.0, "max_seconds": 180.0},
         "scenes": [{"n": 1, "summary": "Two people meet in a plain room."}],
         "cast": [{"entity_id": "lead", "physical": "Tall man, grey eyes."}]}


def test_the_canned_plan_is_a_valid_episode():
    assert Episode.model_validate(canned_plan()).number == 3


# ---- the draft: the contract in a shape a strict provider schema accepts -------------

def test_the_draft_has_exactly_the_contract_s_fields():
    assert set(ew.Draft.model_fields) == set(Episode.model_fields)


def test_the_draft_schema_is_strict_safe_where_the_contract_is_not():
    """A dict field keeps a non-false additionalProperties, which strict structured
    outputs refuse; the draft carries setups as a named list and beds as typed rows."""
    from openai.lib._pydantic import to_strict_json_schema

    def loose(node, path="$"):
        if isinstance(node, dict):
            if node.get("additionalProperties") not in (None, False):
                yield path
            for key, value in node.items():
                yield from loose(value, f"{path}.{key}")
        elif isinstance(node, list):
            for i, value in enumerate(node):
                yield from loose(value, f"{path}[{i}]")

    assert list(loose(to_strict_json_schema(Episode))) != []
    assert list(loose(to_strict_json_schema(ew.Draft))) == []


def test_to_episode_maps_named_setups_and_beds_into_the_contract():
    episode = ew.to_episode(ew.Draft.model_validate(canned_draft()))
    assert isinstance(episode, Episode)
    assert list(episode.setups) == ["room"] and episode.setups["room"].landmark == "the window"
    assert episode.beds == [{"from_shot": 0, "tone": "plain"}]
    assert "name" not in episode.setups["room"].model_dump()


def test_two_setups_with_one_name_are_refused():
    draft = canned_draft()
    draft["setups"].append(dict(draft["setups"][0]))
    with pytest.raises(ValueError, match="twice"):
        ew.to_episode(ew.Draft.model_validate(draft))


def test_the_writer_returns_a_validated_episode():
    fake = FakeModel(canned_draft())
    got = ew.write(BRIEF, _agent=fake)
    assert isinstance(got, Episode) and got.title == "The Yard" and len(got.shots) == N


def test_the_prompt_carries_the_skill_and_the_rendered_brief():
    fake = FakeModel(canned_draft())
    ew.write(BRIEF, _agent=fake)
    prompt = fake.prompts[0]
    assert "episode writer" in prompt.lower()
    assert "Two people meet in a plain room." in prompt
    assert "Tall man, grey eyes." in prompt


def test_the_skill_names_the_one_question():
    assert "which setups, shots, cells, camera moves and lines" in ew.load_skill().lower()


def test_the_skill_is_book_neutral():
    """No book, character or episode name in the desk: the same skill serves every book."""
    text = ew.load_skill().lower()
    for word in ("holmes", "watson", "scarlet", "martian", "wells", "doyle", "ep0", "ep1", "london"):
        assert word not in text, word


def test_without_refusals_the_prompt_has_no_refused_section():
    fake = FakeModel(canned_draft())
    ew.write(BRIEF, _agent=fake)
    assert ew.REFUSED not in fake.prompts[0]


def test_refusals_are_quoted_back_verbatim():
    fake = FakeModel(canned_draft())
    refusals = ["PLAN GATES   : 2", "    G-SCALE shot 4: no cell for a close",
                "MOTION hard  : [(7, 'M2')]"]
    ew.write(BRIEF, refusals=refusals, _agent=fake)
    prompt = fake.prompts[0]
    assert ew.REFUSED in prompt
    tail = prompt[prompt.index(ew.REFUSED):]
    for line in refusals:
        assert line in tail
    assert tail.index(refusals[0]) < tail.index(refusals[1]) < tail.index(refusals[2])


def test_usage_comes_back_with_the_tier():
    usage: dict = {}
    ew.write(BRIEF, usage=usage, _agent=FakeModel(canned_draft()))
    assert usage["tier"] == ew.TIER == "local" and usage["input_tokens"] == 10


def test_a_structured_output_exception_surfaces():
    fake = FakeModel(StructuredOutputException("no structured output"))
    with pytest.raises(StructuredOutputException):
        ew.write(BRIEF, _agent=fake)


def test_a_wrong_shape_surfaces_as_a_structured_output_exception():
    """A payload that fails the draft's shape is a schema violation to the gateway;
    it is retried there and the last refusal is raised, never a raw dict returned."""
    broken = {**canned_draft(), "shots": "not a list"}
    with pytest.raises(StructuredOutputException, match="did not match schema"):
        ew.write(BRIEF, _agent=FakeModel(broken))


def test_a_plan_the_contract_refuses_surfaces_as_a_validation_error():
    """The draft's shape passes; the contract's rules refuse on conversion, the
    writer edits its draft CONTRACT_RETRIES times, then the last refusal is raised."""
    from pydantic import ValidationError
    broken = {**canned_draft(), "lines": []}
    with pytest.raises(ValidationError, match="no button"):
        ew.write(BRIEF, _agent=FakeModel(broken))


def test_the_tier_is_the_local_one():
    assert ew.TIER == "local"
