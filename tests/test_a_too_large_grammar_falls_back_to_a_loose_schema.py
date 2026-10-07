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
