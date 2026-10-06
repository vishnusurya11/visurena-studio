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
        content = json.dumps({"title": "The Pit", "shots": 12})
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
    fmt = client.calls[1][1]["response_format"]
    assert fmt["type"] == "json_schema" and fmt["json_schema"]["strict"] is False
    assert fmt["json_schema"]["schema"]["properties"]["title"]["type"] == "string"
    assert got.metrics.accumulated_usage["inputTokens"] == 10


def test_any_other_400_still_raises():
    with pytest.raises(BadRequestError):
        _caller(FakeClient("Invalid request: bad field"))("write", structured_output_model=Answer)


def test_loose_schema_names_the_model():
    fmt = llm.loose_schema(Answer)
    assert fmt["json_schema"]["name"] == "Answer" and "shots" in fmt["json_schema"]["schema"]["properties"]
