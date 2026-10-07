"""ep20/ep21 (2026-10-06/07): the provider's strict grammar of the WHOLE Draft is
"too large" (every provider, since 17:27Z on the 6th), and the loose path cannot
be made to answer (reasoning is mandatory for the model and eats the budget).
Measured with max_tokens=20 probes: each part compiles, the whole does not; and
a shots+lines body, though it compiled, ground at the provider for 33 minutes.
So one draft is PARTS strict calls in order -- the frame (scalars, setups,
beds), the shots, the lines -- each reading the merged earlier parts, merged and
validated as the one Draft the contract judges.  $0."""
from __future__ import annotations

from agents import episode_writer as ew
from studio.episode_spec import Episode
from tests.test_episode_writer import BRIEF, FakeModel, canned_draft


def _draft(number: int = 3) -> dict:
    return ew.Draft.model_validate(canned_draft(number)).model_dump()


def _parts(doc: dict) -> list:
    return [model.model_validate({k: doc[k] for k in fields if k in doc})
            for (_, fields), model in zip(ew.PART_TABLE, ew.PART_MODELS)]


def test_the_parts_cover_the_draft_exactly_once():
    fields = [f for _, part in ew.PART_TABLE for f in part]
    assert set(fields) == set(ew.Draft.model_fields) and len(fields) == len(set(fields))
    assert ew.PARTS == len(ew.PART_TABLE) == len(ew.PART_MODELS) == 3


def test_one_draft_is_parts_strict_calls_each_reading_the_earlier_ones():
    parts = _parts(_draft())
    model = FakeModel(*parts)
    got = ew.write(BRIEF, _agent=model)
    assert isinstance(got, Episode) and len(model.prompts) == ew.PARTS
    assert ew.PART_FRAME in model.prompts[0] and ew.PART_SHOTS in model.prompts[1] and ew.PART_LINES in model.prompts[2]
    setup_name = parts[0].model_dump()["setups"][0]["name"]
    assert setup_name in model.prompts[1] and setup_name in model.prompts[2]
    assert '"shots"' in model.prompts[2] and '"shots"' not in model.prompts[1].split(ew.PART_SHOTS)[1]


def test_refusals_and_the_previous_plan_reach_every_part():
    model = FakeModel(*_parts(_draft()))
    ew.write(BRIEF, refusals=["G-X shot 1: too long"], previous=_draft(), _agent=model)
    for prompt in model.prompts:
        assert "G-X shot 1" in prompt and ew.PREVIOUS in prompt


def test_usage_sums_every_part():
    usage: dict = {}
    ew.write(BRIEF, usage=usage, _agent=FakeModel(*_parts(_draft())))
    assert usage["input_tokens"] == 10 * ew.PARTS and usage["output_tokens"] == 5 * ew.PARTS


def test_a_part_that_breaks_the_contract_is_re_asked_with_the_refusal():
    frame, shots, lines = _parts(_draft())
    bad = lines.model_copy(deep=True)
    bad.lines[0].shot = 99                                   # names a shot that does not exist
    model = FakeModel(frame, shots, bad, frame, shots, lines)
    got = ew.write(BRIEF, _agent=model)
    assert isinstance(got, Episode) and len(model.prompts) == 2 * ew.PARTS
    assert ew.REFUSED in model.prompts[ew.PARTS]


def test_a_fake_that_answers_the_whole_draft_still_serves_each_part():
    """Every older writer test's FakeModel returns a whole Draft; each part
    validates its own fields out of it (llm._validated takes a superset model)."""
    got = ew.write(BRIEF, _agent=FakeModel(ew.Draft.model_validate(_draft())))
    assert isinstance(got, Episode)


def test_a_slow_word_in_a_part_is_stripped_before_the_contract_judges_it():
    """ep22 (2026-10-07): luna wrote 'slowly' in three motions; the shots part was
    refused three times a rung by the contract's rule and the draft never landed,
    so the free `strip_slow` cure (L3) never got its turn.  The cure runs on the
    part's raw text first; the contract then judges the cured text."""
    from types import SimpleNamespace
    doc = _draft()
    frame = ew.PartFrame.model_validate({k: doc[k] for k in ew.FRAME_FIELDS})
    lines = ew.PartLines.model_validate({k: doc[k] for k in ew.LINE_FIELDS})
    slow = {"shots": [dict(s, motion="The camera drifts slowly left.") if i == 0 else s
                      for i, s in enumerate(doc["shots"])]}
    calls = []

    class Fake:
        def __call__(self, prompt, structured_output_model=None):
            calls.append(structured_output_model.__name__)
            payload = {ew.PartFrame: frame, ew.PartShots: slow, ew.PartLines: lines}[structured_output_model]
            return SimpleNamespace(structured_output=payload, metrics=SimpleNamespace(
                accumulated_usage={"inputTokens": 1, "outputTokens": 1, "totalTokens": 2}))

    got = ew.write(BRIEF, _agent=Fake())
    assert isinstance(got, Episode) and calls == ["PartFrame", "PartShots", "PartLines"]
    assert "slowly" not in got.shots[0].motion and "drifts left" in got.shots[0].motion
