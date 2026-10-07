"""ep20 (2026-10-06, the autopilot's first launch): the writer's structured call
died in 30 s with a 400 from every provider behind OpenRouter -- "The compiled
grammar is too large ... Simplify your tool schemas or reduce the number of
strict tools".  The Episode schema is big; strict decoding compiles it to a
grammar the provider now refuses.  The caller retries ONCE with the same
schema sent loose (strict=False) and validates the JSON itself; any other 400
still raises.  $0: a fake client."""
from __future__ import annotations

import json
from types import SimpleNamespace

import httpx
import pytest
from openai import BadRequestError
from pydantic import BaseModel

from studio import llm

TOO_LARGE = "The compiled grammar is too large, which would cause performance issues."


@pytest.fixture(autouse=True)
def _fresh_memo():
    llm.STRICT_REFUSED.clear()
    yield
    llm.STRICT_REFUSED.clear()


class Answer(BaseModel):
    title: str
    shots: int


def _400(message: str) -> BadRequestError:
    response = httpx.Response(400, request=httpx.Request("POST", "https://x/v1/chat/completions"))
    return BadRequestError(message, response=response, body={"error": {"message": message}})


class FakeClient:
    """`parse` refuses the strict grammar; `create` answers the loose one."""

    def __init__(self, message: str = TOO_LARGE):
        self.message, self.calls = message, []
        self.chat = SimpleNamespace(completions=SimpleNamespace(parse=self.parse, create=self.create))

    def parse(self, **kw):
        self.calls.append(("parse", kw))
        raise _400(self.message)

    def create(self, **kw):
        self.calls.append(("create", kw))
        if "response_format" in kw:                      # ep21: OpenRouter makes ANY json_schema a strict tool
            raise _400(self.message)
        content = "```json\n" + json.dumps({"title": "The Pit", "shots": 12}) + "\n```"
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))],
                               usage=SimpleNamespace(prompt_tokens=10, completion_tokens=5, total_tokens=15))


def _caller(client):
    caller = llm._NativeStructuredCaller.__new__(llm._NativeStructuredCaller)
    caller._client, caller._model, caller._params, caller._tier = client, "m", {}, "local"
    return caller


def test_too_large_grammar_is_retried_loose_and_validated():
    client = FakeClient()
    got = _caller(client)("write", structured_output_model=Answer)
    assert got.structured_output == Answer(title="The Pit", shots=12)
    assert [c[0] for c in client.calls] == ["parse", "create"]
    kw = client.calls[1][1]
    assert "response_format" not in kw, "ep21: a json_schema response_format is a strict tool on OpenRouter"
    prompt = kw["messages"][-1]["content"]
    assert '"shots"' in prompt and "JSON" in prompt and prompt.startswith("write")
    assert got.metrics.accumulated_usage["inputTokens"] == 10


def test_a_fenced_or_prefixed_reply_is_still_json():
    assert llm.json_body('```json\n{"a": 1}\n```') == '{"a": 1}'
    assert llm.json_body('Here it is:\n{"a": 1}') == '{"a": 1}'


def test_any_other_400_still_raises():
    with pytest.raises(BadRequestError):
        _caller(FakeClient("Invalid request: bad field"))("write", structured_output_model=Answer)


def test_the_schema_prompt_carries_the_model_schema():
    text = llm.schema_prompt("write", Answer)
    assert text.startswith("write") and '"shots"' in text and "Answer" in text


def test_the_loose_call_asks_for_a_whole_plan_of_output():
    """ep21 (2026-10-07): without a response_format the provider defaulted
    max_tokens to ~4k and the 12-16k-token plan came back cut off at column
    10521 -- 'Invalid JSON: EOF while parsing a list', three paid rounds."""
    client = FakeClient()
    _caller(client)("write", structured_output_model=Answer)
    assert client.calls[1][1]["max_tokens"] >= llm.LOOSE_MAX_TOKENS >= 16_000


class NoContentClient(FakeClient):
    """ep21 relaunch (2026-10-07): the loose reply came back with content None."""

    def create(self, **kw):
        self.calls.append(("create", kw))
        choice = SimpleNamespace(message=SimpleNamespace(content=None), finish_reason="error",
                                 error={"message": "provider overloaded", "code": 502})
        return SimpleNamespace(choices=[choice], usage=SimpleNamespace(prompt_tokens=48000, completion_tokens=32000))


def test_a_reply_without_content_is_a_refusal_that_carries_its_usage():
    """ep21 (2026-10-07): three reasoning-only replies and three cut-off plans were
    paid for and never ledgered -- the $3 wall under-counted ~$1.8.  A failed paid
    call is a StructuredOutputException (re-asked like any refusal) that carries
    the tokens it cost."""
    from strands.types.exceptions import StructuredOutputException
    with pytest.raises(StructuredOutputException) as caught:
        _caller(NoContentClient())("write", structured_output_model=Answer)
    assert "finish_reason=error" in str(caught.value) and "overloaded" in str(caught.value)
    assert caught.value.usage == {"input_tokens": 48000, "output_tokens": 32000}


class CutClient(FakeClient):
    def create(self, **kw):
        self.calls.append(("create", kw))
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content='{"title": "The Pit", "sho'))],
                               usage=SimpleNamespace(prompt_tokens=10, completion_tokens=4000))


def test_a_cut_off_plan_is_a_refusal_that_carries_its_usage():
    from strands.types.exceptions import StructuredOutputException
    with pytest.raises(StructuredOutputException) as caught:
        _caller(CutClient())("write", structured_output_model=Answer)
    assert caught.value.usage["output_tokens"] == 4000


def test_every_failed_paid_attempt_is_ledgered(tmp_path):
    from strands.types.exceptions import StructuredOutputException
    from studio import db, spend

    class Refuser:
        def __call__(self, prompt, structured_output_model=None):
            exc = StructuredOutputException("cut off")
            exc.usage = {"input_tokens": 100, "output_tokens": 50}
            raise exc

    conn = db.get_connection(tmp_path / "t.db")
    db.init_db(conn)
    with llm.spend_context(conn, "2099", "episode", "02", unit="ep01"):
        with pytest.raises(StructuredOutputException):
            llm.structured("workhorse", "write", Answer, retries=2, _agent=Refuser())
    rows = conn.execute("select input_tokens, output_tokens, cost_usd from usage where unit='ep01'").fetchall()
    assert [tuple(r)[:2] for r in rows] == [(100, 50), (100, 50)] and all(r[2] is not None for r in rows)
    assert spend.unit_spent(conn, "2099", "ep01") > 0


def test_a_model_whose_strict_grammar_was_refused_goes_loose_at_once():
    """The strict probe cost ep21 ~25 min while OpenRouter cycled three providers
    before the 400; once a model has refused the grammar, the next call on it
    skips the probe."""
    llm.STRICT_REFUSED.discard("m")
    first = FakeClient()
    _caller(first)("write", structured_output_model=Answer)
    assert [c[0] for c in first.calls] == ["parse", "create"] and "m" in llm.STRICT_REFUSED
    second = FakeClient()
    _caller(second)("write", structured_output_model=Answer)
    assert [c[0] for c in second.calls] == ["create"]
    llm.STRICT_REFUSED.discard("m")


def test_a_tier_marked_loose_never_probes_the_strict_grammar(monkeypatch):
    """The memo is per process and every drive run is a new process: without a
    tier setting each relaunch re-paid the ~25-min probe (ep21, 2026-10-07)."""
    monkeypatch.setattr(llm, "resolve_tier", lambda tier: {
        "provider": "openrouter", "model": "m", "params": {}, "structured_output": "loose",
        "provider_config": {"base_url": "https://x/v1", "api_key_env": "NOPE"}})
    monkeypatch.setattr(llm, "_api_key", lambda pc: "k")
    caller = llm._NativeStructuredCaller("local")
    client = FakeClient()
    caller._client = client
    caller("write", structured_output_model=Answer)
    assert [c[0] for c in client.calls] == ["create"]


def test_the_loose_call_caps_reasoning_and_leaves_room_for_the_plan():
    """ep21 (2026-10-07): the loose reply came back finish_reason=length,
    reasoning=yes, content None -- the model spent the whole output budget
    thinking; and OpenRouter refuses to disable reasoning for it ("mandatory for
    this endpoint").  So the thought is capped small and the answer gets the rest."""
    client = FakeClient()
    _caller(client)("write", structured_output_model=Answer)
    kw = client.calls[1][1]
    budget = kw["extra_body"]["reasoning"]["max_tokens"]
    assert 1024 <= budget <= 4096 and kw["max_tokens"] - budget >= 16_000
