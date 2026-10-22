"""Claude is never wrapped as a Strands Model (group R ruling A10(b), 2026-10-22): a
claude-sdk tier is one Agent SDK session per call through `_SdkStructuredCaller`.
A Strands wrapper would stack its own retries on the CLI's and llm.structured's
(6 x 3 x 10 calls, r1_strands) and hide the session id and usage the ledger reads.
A regression pin: it was green when written."""
from __future__ import annotations

from strands import Agent

from studio import llm


def test_a_claude_sdk_tier_gets_the_sdk_caller_not_a_strands_agent(monkeypatch):
    monkeypatch.setattr(llm, "resolve_tier", lambda tier: {
        "model": "claude-sonnet-5", "provider": "claude-sdk", "params": {"effort": "low"},
        "structured_output": None, "timeout_s": None, "provider_config": {}})
    caller = llm._caller_for("workhorse")
    assert isinstance(caller, llm._SdkStructuredCaller) and not isinstance(caller, Agent)
