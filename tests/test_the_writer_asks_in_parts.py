"""ep20/ep21 (2026-10-06/07): the provider's strict grammar of the WHOLE Draft is
"too large" (every provider, since 17:27Z on the 6th), and the loose path cannot
be made to answer (reasoning is mandatory for the model and eats the budget).
Measured with max_tokens=20 probes: `Draft minus shots` compiles, `shots + lines +
beds` compiles, the whole does not.  So one draft is TWO strict calls -- the
FRAME (scalars, setups, beds) and the BODY (shots, lines), the body reading the
frame -- merged and validated as the one Draft the contract judges.  $0."""
from __future__ import annotations

import json

from agents import episode_writer as ew
from studio.episode_spec import Episode
from tests.test_episode_writer import BRIEF, FakeModel, canned_draft


def _draft(number: int = 3) -> dict:
    return ew.Draft.model_validate(canned_draft(number)).model_dump()


def _parts(doc: dict):
    frame = ew.PartFrame.model_validate({k: doc[k] for k in ew.FRAME_FIELDS if k in doc})
    body = ew.PartBody.model_validate({k: doc[k] for k in ew.BODY_FIELDS if k in doc})
    return frame, body


def test_the_parts_cover_the_draft_exactly_once():
    assert set(ew.FRAME_FIELDS) | set(ew.BODY_FIELDS) == set(ew.Draft.model_fields)
    assert not set(ew.FRAME_FIELDS) & set(ew.BODY_FIELDS)
    assert "shots" in ew.BODY_FIELDS and "setups" in ew.FRAME_FIELDS and "lines" in ew.BODY_FIELDS


def test_one_draft_is_two_strict_calls_the_body_reading_the_frame():
    frame, body = _parts(_draft())
    model = FakeModel(frame, body)
    got = ew.write(BRIEF, _agent=model)
    assert isinstance(got, Episode) and len(model.prompts) == 2
    assert ew.PART_FRAME in model.prompts[0] and ew.PART_BODY in model.prompts[1]
    assert json.dumps(frame.model_dump()["setups"][0]["name"]) in model.prompts[1] or \
        frame.model_dump()["setups"][0]["name"] in model.prompts[1]


def test_refusals_and_the_previous_plan_reach_every_part():
    frame, body = _parts(_draft())
    model = FakeModel(frame, body)
    ew.write(BRIEF, refusals=["G-X shot 1: too long"], previous=_draft(), _agent=model)
    for prompt in model.prompts:
        assert "G-X shot 1" in prompt and ew.PREVIOUS in prompt


def test_usage_sums_both_parts():
    frame, body = _parts(_draft())
    usage: dict = {}
    ew.write(BRIEF, usage=usage, _agent=FakeModel(frame, body))
    assert usage["input_tokens"] == 20 and usage["output_tokens"] == 10


def test_a_body_that_breaks_the_contract_is_re_asked_with_the_refusal():
    frame, body = _parts(_draft())
    bad = body.model_copy(deep=True)
    bad.lines[0].shot = 99                                   # names a shot that does not exist
    model = FakeModel(frame, bad, frame, body)
    got = ew.write(BRIEF, _agent=model)
    assert isinstance(got, Episode) and len(model.prompts) == 4
    assert ew.REFUSED in model.prompts[2]


def test_a_fake_that_answers_the_whole_draft_still_serves_each_part():
    """Every older writer test's FakeModel returns a whole Draft; each part
    validates its own fields out of it (llm._validated takes a superset model)."""
    whole = ew.Draft.model_validate(_draft())
    got = ew.write(BRIEF, _agent=FakeModel(whole))
    assert isinstance(got, Episode)
