"""Owner, 2026-10-07: "don't use API for money -- use Claude, like how you used to
supervise."  Every LLM tier runs on the Claude Agent SDK under the owner's
subscription: one structured session per call, the schema enforced by the SDK,
no API key, no grammar limit, no $3 wall (nothing is billed; tokens are still
ledgered with a NULL cost so the wall ignores them).  $0: a fake transport."""
from __future__ import annotations

from types import SimpleNamespace

import anyio
import pytest
from pydantic import BaseModel

from studio import brain, db, llm, spend
from tests.test_brain_a_verdict_is_read_from_the_result_never_from_prose import FakeTransport, result_row


class Answer(BaseModel):
    title: str
    shots: int


def test_ask_structured_returns_the_schema_instance_and_the_receipt():
    transport = FakeTransport([result_row({"title": "The Pit", "shots": 12})])

    async def one():
        return await brain.ask_structured("Plan it.", Answer, model="claude-opus-5-5", transport=transport)

    got, receipt = anyio.run(one)
    assert got == Answer(title="The Pit", shots=12)
    assert receipt["model_usage"] and receipt["session_id"] == "sess-1"
    # the schema rides on the CLI's argv (--json-schema), not over the stdin initialize


def test_the_sdk_caller_answers_the_structured_protocol(monkeypatch):
    seen = {}

    async def fake_ask(prompt, schema, *, model, effort="medium", transport=None):
        seen.update(prompt=prompt, schema=schema, model=model, effort=effort)
        return Answer(title="x", shots=1), {"model_usage": {model: {"input_tokens": 40, "output_tokens": 9}}}

    monkeypatch.setattr(brain, "ask_structured", fake_ask)
    monkeypatch.setattr(llm, "resolve_tier", lambda tier: {
        "provider": "claude-sdk", "model": "claude-opus-5-5", "params": {"effort": "high"}, "structured_output": None,
        "timeout_s": None, "provider_config": {"billing": "subscription"}})
    caller = llm._SdkStructuredCaller("local")
    got = caller("Plan it.", structured_output_model=Answer)
    assert got.structured_output == Answer(title="x", shots=1)
    assert got.metrics.accumulated_usage == {"inputTokens": 40, "outputTokens": 9, "totalTokens": 49}
    assert seen["model"] == "claude-opus-5-5" and seen["effort"] == "high" and seen["schema"] is Answer


def test_structured_picks_the_sdk_caller_ledgers_at_no_cost_and_never_guards(monkeypatch, tmp_path):
    async def fake_ask(prompt, schema, *, model, effort="medium", transport=None):
        return Answer(title="x", shots=1), {"model_usage": {model: {"input_tokens": 40, "output_tokens": 9}}}

    monkeypatch.setattr(brain, "ask_structured", fake_ask)
    monkeypatch.setattr(llm, "resolve_tier", lambda tier: {
        "provider": "claude-sdk", "model": "claude-opus-5-5", "params": {}, "structured_output": None,
        "timeout_s": None, "provider_config": {"billing": "subscription"}})
    monkeypatch.setattr(llm, "guard_spend", lambda *a, **k: (_ for _ in ()).throw(AssertionError("guard called")))
    conn = db.get_connection(tmp_path / "t.db")
    db.init_db(conn)
    with llm.spend_context(conn, "2099", "episode", "02", unit="ep19"):
        got = llm.structured("local", "Plan it.", Answer)
    assert got == Answer(title="x", shots=1)
    row = conn.execute("select model, input_tokens, output_tokens, cost_usd from usage").fetchone()
    assert tuple(row)[:3] == ("claude-opus-5-5@subscription", 40, 9) and row[3] is None
    assert spend.unit_spent(conn, "2099", "ep19") == 0.0


def test_every_tier_in_models_yaml_runs_on_the_subscription():
    config = llm.load_models_config()
    for name, tier in config["tiers"].items():
        assert tier["provider"] == "claude-sdk", f"tier {name} still pays an API"
    assert config["providers"]["claude-sdk"]["billing"] == "subscription"
