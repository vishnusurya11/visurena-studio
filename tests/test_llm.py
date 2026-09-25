"""Tests for studio.llm — tier config + structured-output gateway.

Per CLAUDE.md: no test calls a paid API. The agent is always faked; we test the
CONTRACT: config resolution, schema validation, retry on StructuredOutputException.
"""

from __future__ import annotations

import pytest
from pydantic import BaseModel
from strands.types.exceptions import StructuredOutputException

from studio import llm


class Toy(BaseModel):
    answer: str


class FakeResult:
    def __init__(self, obj):
        self.structured_output = obj


class FakeAgent:
    """Scriptable agent: raises for the first `fail_times` calls, then succeeds."""

    def __init__(self, obj, fail_times=0):
        self.obj = obj
        self.fail_times = fail_times
        self.calls = 0

    def __call__(self, prompt, structured_output_model=None):
        self.calls += 1
        if self.calls <= self.fail_times:
            raise StructuredOutputException("schema mismatch")
        return FakeResult(self.obj)


# --- config ---


def test_tiers_load_from_models_yaml():
    config = llm.load_models_config()
    assert "workhorse" in config["tiers"]
    assert config["tiers"]["workhorse"]["provider"] in config["providers"]


def test_unknown_tier_is_loud():
    with pytest.raises(ValueError, match="unknown tier"):
        llm.resolve_tier("nonexistent_tier")


def test_resolve_tier_returns_provider_and_model():
    resolved = llm.resolve_tier("workhorse")
    assert resolved["model"]
    assert "api_key_env" in resolved["provider_config"]


# --- structured() contract ---


def test_structured_returns_validated_object():
    fake = FakeAgent(Toy(answer="42"))
    result = llm.structured("workhorse", "prompt", Toy, _agent=fake)
    assert result.answer == "42"
    assert fake.calls == 1


def test_structured_retries_on_schema_violation():
    fake = FakeAgent(Toy(answer="ok"), fail_times=2)
    result = llm.structured("workhorse", "prompt", Toy, _agent=fake, retries=3)
    assert result.answer == "ok"
    assert fake.calls == 3  # two failures + one success


def test_structured_raises_after_max_retries():
    fake = FakeAgent(Toy(answer="never"), fail_times=99)
    with pytest.raises(StructuredOutputException):
        llm.structured("workhorse", "prompt", Toy, _agent=fake, retries=2)
    assert fake.calls == 2


# --- usage tracking ---


class FakeMetrics:
    accumulated_usage = {"inputTokens": 4200, "outputTokens": 310, "totalTokens": 4510}


class FakeResultWithUsage(FakeResult):
    metrics = FakeMetrics()


class FakeAgentWithUsage(FakeAgent):
    def __call__(self, prompt, structured_output_model=None):
        self.calls += 1
        return FakeResultWithUsage(self.obj)


def test_structured_fills_usage_dict():
    usage = {}
    llm.structured("workhorse", "p", Toy, _agent=FakeAgentWithUsage(Toy(answer="x")),
                   usage=usage)
    assert usage == {"input_tokens": 4200, "output_tokens": 310, "total_tokens": 4510,
                     "tier": "workhorse"}


def test_structured_usage_survives_unknown_result_shape():
    usage = {}
    llm.structured("workhorse", "p", Toy, _agent=FakeAgent(Toy(answer="x")), usage=usage)
    assert usage["tier"] == "workhorse"          # never crashes on missing metrics
    assert usage.get("input_tokens", 0) == 0


# --- structured output is GUARANTEED: None / wrong shape never escapes ---


class FakeAgentReturningNone(FakeAgent):
    """Model 'succeeded' but produced no structured output — must be treated as failure."""

    def __call__(self, prompt, structured_output_model=None):
        self.calls += 1
        if self.calls <= self.fail_times:
            return FakeResult(None)
        return FakeResult(self.obj)


def test_none_structured_output_is_retried_then_recovers():
    fake = FakeAgentReturningNone(Toy(answer="ok"), fail_times=1)
    result = llm.structured("workhorse", "p", Toy, _agent=fake, retries=3)
    assert result.answer == "ok"
    assert fake.calls == 2


def test_none_structured_output_exhausts_retries_loudly():
    fake = FakeAgentReturningNone(Toy(answer="never"), fail_times=99)
    with pytest.raises(StructuredOutputException, match="no structured output"):
        llm.structured("workhorse", "p", Toy, _agent=fake, retries=2)


def test_wrong_type_output_is_revalidated_into_schema():
    fake = FakeAgent({"answer": "as dict"})  # raw dict instead of Toy instance
    result = llm.structured("workhorse", "p", Toy, _agent=fake)
    assert isinstance(result, Toy)
    assert result.answer == "as dict"


def test_invalid_shape_output_is_retried():
    fake = FakeAgent({"wrong_field": 1}, fail_times=0)
    with pytest.raises(StructuredOutputException, match="did not match schema"):
        llm.structured("workhorse", "p", Toy, _agent=fake, retries=2)
    assert fake.calls == 2


# --- per-tier params passthrough (model quirks live in models.yaml, not code) ---


def test_resolve_tier_carries_params():
    resolved = llm.resolve_tier("workhorse")
    assert resolved["params"].get("reasoning_effort") == "none"  # Luna quirk, in config


def test_model_kwargs_includes_params():
    resolved = {"model": "m", "provider": "openai", "params": {"reasoning_effort": "none"},
                "provider_config": {"base_url": "http://x", "api_key_env": None}}
    kwargs = llm._model_kwargs(resolved)
    assert kwargs["model_id"] == "m"
    assert kwargs["params"] == {"reasoning_effort": "none"}


def test_model_kwargs_omits_empty_params():
    resolved = {"model": "m", "provider": "openai", "params": {},
                "provider_config": {"base_url": "http://x", "api_key_env": None}}
    assert "params" not in llm._model_kwargs(resolved)


# --- transient-error resilience (real-run failure 2026-08-23: EventLoopException) ---


class FlakyAgent(FakeAgent):
    """Raises transient errors before succeeding."""

    def __call__(self, prompt, structured_output_model=None):
        self.calls += 1
        if self.calls <= self.fail_times:
            raise RuntimeError("Connection error.")
        return FakeResult(self.obj)


def test_transient_errors_are_retried_with_backoff(monkeypatch):
    sleeps = []
    monkeypatch.setattr(llm.time, "sleep", sleeps.append)
    fake = FlakyAgent(Toy(answer="ok"), fail_times=2)
    result = llm.structured("workhorse", "p", Toy, _agent=fake)
    assert result.answer == "ok"
    assert fake.calls == 3
    assert len(sleeps) == 2          # backed off between attempts


def test_transient_errors_exhaust_loudly(monkeypatch):
    monkeypatch.setattr(llm.time, "sleep", lambda s: None)
    fake = FlakyAgent(Toy(answer="never"), fail_times=99)
    with pytest.raises(RuntimeError, match="Connection error"):
        llm.structured("workhorse", "p", Toy, _agent=fake, transient_retries=2)
    assert fake.calls == 3           # 1 + 2 retries


class Recorder(FakeAgent):
    """FakeAgent that keeps every prompt it was asked."""

    def __init__(self, obj, fail_times=0):
        super().__init__(obj, fail_times)
        self.prompts = []

    def __call__(self, prompt, structured_output_model=None):
        self.prompts.append(prompt)
        return super().__call__(prompt, structured_output_model)


def test_a_retry_carries_the_refusal_back_to_the_model():
    """Episode 13, 2026-09-25: five rungs of from-scratch drafts, each refused on a
    rule the skill states, because a re-ask repeated the same prompt and the
    model never heard what was wrong."""
    fake = Recorder(Toy(answer="ok"), fail_times=1)
    llm.structured("workhorse", "prompt", Toy, _agent=fake, retries=3)
    assert fake.prompts[0] == "prompt"
    assert fake.prompts[1].startswith("prompt") and llm.REFUSED in fake.prompts[1]
    assert "schema mismatch" in fake.prompts[1]


def test_every_re_ask_quotes_the_latest_refusal_over_the_original_prompt():
    fake = Recorder(Toy(answer="ok"), fail_times=2)
    llm.structured("workhorse", "prompt", Toy, _agent=fake, retries=3)
    assert fake.prompts[2].count(llm.REFUSED) == 1 and fake.prompts[2].startswith("prompt")


def test_the_native_caller_turns_a_pydantic_refusal_into_a_schema_violation():
    """`chat.completions.parse` validates the model's JSON itself; a contract rule
    that refuses inside the schema is a schema violation to the gateway, retried
    there, never a transient failure slept on."""
    caller = object.__new__(llm._NativeStructuredCaller)
    caller._parse = lambda prompt, model: Toy.model_validate({"answer": 5})
    with pytest.raises(StructuredOutputException, match="did not match schema"):
        caller("prompt", Toy)
