"""One brain turn is one Claude Agent SDK session; the verdict is the result's
structured JSON, never its prose (decision 2026-10-06, Layer 2).  The session is
driven through a fake Transport -- the SDK's own seam for custom transports -- that
answers the control protocol and yields canned stream-json, so no test spends.

A result without structured output, an error subtype, or a terminal reason other
than `completed` is a failure the supervisor sees as an exception, not a verdict it
could misread.  A rejected rate limit surfaces as RateLimited(resets_at) so the
supervisor can sleep until the window opens."""
from __future__ import annotations

import json
from collections.abc import AsyncIterator
from pathlib import Path

import anyio
import pytest
from claude_agent_sdk._internal.transport import Transport

from studio import brain

REPO = Path(__file__).resolve().parents[1]


def result_row(structured=None, **over) -> dict:
    """A stream-json `result` the way the CLI writes it (modelUsage is camelCase)."""
    row = {"type": "result", "subtype": "success", "duration_ms": 10, "duration_api_ms": 8,
           "is_error": False, "num_turns": 2, "session_id": "sess-1", "total_cost_usd": 0.25,
           "structured_output": structured,
           "modelUsage": {"claude-sonnet-5-5": {"inputTokens": 1000, "outputTokens": 200,
                                                "cacheReadInputTokens": 50,
                                                "cacheCreationInputTokens": 0, "costUSD": 0.25}}}
    return {**row, **over}


def verdict_json(**over) -> dict:
    return {"response": "cure", "order": {"kind": "redo", "step_id": "08"},
            "reason": "the grid judge parked on a stale cell",
            "finding_row": "| F21 | ep20 step 08 | 0 | redo 08 | open |", **over}


class FakeTransport(Transport):
    """Answers every control request with success and, on the user's message, yields
    the canned replies.  Implements the full Transport ABC of claude-agent-sdk 0.2.159."""

    def __init__(self, replies: list[dict]):
        self.replies, self.writes, self._ready = replies, [], False
        self._send, self._recv = anyio.create_memory_object_stream(64)

    async def connect(self) -> None:
        self._ready = True

    async def write(self, data: str) -> None:
        message = json.loads(data)
        self.writes.append(message)
        if message.get("type") == "control_request":
            await self._send.send({"type": "control_response", "response": {
                "subtype": "success", "request_id": message["request_id"], "response": {}}})
        elif message.get("type") == "user":
            for reply in self.replies:
                await self._send.send(reply)

    async def read_messages(self) -> AsyncIterator[dict]:
        async with self._recv:
            async for message in self._recv:
                yield message

    async def close(self) -> None:
        self._ready = False
        await self._send.aclose()

    def is_ready(self) -> bool:
        return self._ready

    async def end_input(self) -> None:
        pass


def run_turn(replies: list[dict], options=None):
    transport = FakeTransport(replies)
    options = options or brain.triage_options(REPO)
    async def one_turn():
        return await brain.turn("why did ep20 park?", options, transport=transport)
    return anyio.run(one_turn), transport


def test_the_verdict_is_the_results_structured_output():
    (verdict, receipt), transport = run_turn([result_row(verdict_json())])
    assert verdict.response == "cure" and verdict.order == {"kind": "redo", "step_id": "08"}
    assert verdict.finding_row.startswith("| F21 |")
    assert receipt["session_id"] == "sess-1" and receipt["total_cost_usd"] == 0.25
    assert receipt["model_usage"]["claude-sonnet-5-5"] == {"input_tokens": 1050, "output_tokens": 200}


def test_the_prompt_reaches_the_session_as_the_user_message():
    _, transport = run_turn([result_row(verdict_json())])
    users = [w for w in transport.writes if w.get("type") == "user"]
    assert len(users) == 1 and "why did ep20 park?" in json.dumps(users[0])


def test_a_result_without_structured_output_is_a_failure_not_a_guess():
    with pytest.raises(brain.BrainFailed, match="structured"):
        run_turn([result_row(None, result="I think you should retry.")])


def test_an_error_subtype_is_a_failure():
    with pytest.raises(brain.BrainFailed, match="error_max_turns"):
        run_turn([result_row(verdict_json(), subtype="error_max_turns", is_error=True)])


def test_a_terminal_reason_other_than_completed_is_a_failure_even_on_a_success_subtype():
    with pytest.raises(brain.BrainFailed, match="api_error"):
        run_turn([result_row(verdict_json(), terminal_reason="api_error")])


def test_a_rejected_rate_limit_says_when_the_window_resets():
    event = {"type": "rate_limit_event", "uuid": "u1", "session_id": "sess-1",
             "rate_limit_info": {"status": "rejected", "resetsAt": 1_800_000_000,
                                 "rateLimitType": "five_hour"}}
    with pytest.raises(brain.RateLimited) as caught:
        run_turn([event, result_row(verdict_json())])
    assert caught.value.resets_at == 1_800_000_000


def test_a_rate_limit_warning_does_not_stop_the_turn():
    event = {"type": "rate_limit_event", "uuid": "u1", "session_id": "sess-1",
             "rate_limit_info": {"status": "allowed_warning", "resetsAt": 1}}
    (verdict, _), _ = run_turn([event, result_row(verdict_json())])
    assert verdict.response == "cure"


def test_a_verdict_outside_the_contract_is_refused_by_the_schema():
    with pytest.raises(Exception, match="response"):
        run_turn([result_row(verdict_json(response="ship"))])
