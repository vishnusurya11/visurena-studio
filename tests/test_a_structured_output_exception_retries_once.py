"""A reading the caller cannot shape is asked for once more, then it surfaces:
the critic never loops, and never returns fewer readings than it was asked
for without raising."""
from __future__ import annotations

import pytest
from strands.types.exceptions import StructuredOutputException

from agents import plan_reader
from tests.plan_reader_fixtures import reading_dict
from tests.test_episode_writer import FakeModel


def test_one_schema_violation_is_retried_and_the_reading_comes_back():
    fake = FakeModel(StructuredOutputException("no structured output"), reading_dict("good"))
    got = plan_reader.read("plan", ["row"], k=1, _agent=fake)
    assert len(got) == 1 and got[0].turn.shot == 14
    assert len(fake.prompts) == 2


def test_a_second_violation_surfaces_after_exactly_one_retry():
    fake = FakeModel(StructuredOutputException("no structured output"))
    with pytest.raises(StructuredOutputException):
        plan_reader.read("plan", ["row"], k=1, _agent=fake)
    assert len(fake.prompts) == plan_reader.RETRIES == 2


def test_a_wrong_shape_is_a_schema_violation_too():
    fake = FakeModel({"turn": "not a turn"})
    with pytest.raises(StructuredOutputException, match="did not match schema"):
        plan_reader.read("plan", ["row"], k=1, _agent=fake)


def test_usage_is_the_sum_over_the_k_asks():
    usage: dict = {}
    plan_reader.read("plan", ["row"], k=3, usage=usage, _agent=FakeModel(reading_dict("good")))
    assert usage["input_tokens"] == 30 and usage["output_tokens"] == 15 and usage["tier"] == plan_reader.TIER
