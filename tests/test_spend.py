"""Token usage is recorded, priced, and queryable. No API calls; no spend.

Every cost figure quoted in this project so far has been an estimate, because nothing
persisted usage: 64 log files, zero usage records. `_extract_usage` existed and each
step logged its numbers to text, which is unreadable in aggregate and silently absent
whenever a step forgot to pass `usage={}`.

So recording happens at the GATEWAY, not in the steps. A step cannot forget.
"""

from __future__ import annotations

import pytest

from studio import db, spend


@pytest.fixture()
def conn(tmp_path):
    connection = db.get_connection(tmp_path / "spend.db")
    db.init_db(connection)
    db.insert_codex(connection, "Test Book", codex_id="20260825120000")
    return connection


def _record(connection, **over):
    row = dict(codex_id="20260825120000", stage="screenplay", step_id="03",
               tier="workhorse", model="gpt-5.6-luna",
               input_tokens=10_000, output_tokens=2_000)
    return spend.record(connection, **{**row, **over})


# --- recording ---------------------------------------------------------------------

def test_a_call_is_recorded(conn):
    _record(conn)
    assert spend.total(conn, "20260825120000")["calls"] == 1


def test_tokens_accumulate_across_calls(conn):
    for _ in range(3):
        _record(conn)
        totals = spend.total(conn, "20260825120000")
    assert totals["input_tokens"] == 30_000 and totals["output_tokens"] == 6_000


def test_cost_is_computed_from_the_rate_table(conn):
    _record(conn, input_tokens=1_000_000, output_tokens=1_000_000)
    # luna: $0.20 per M in, $1.20 per M out
    assert spend.total(conn, "20260825120000")["cost_usd"] == pytest.approx(1.40)


def test_an_unpriced_model_records_tokens_and_a_null_cost(conn):
    """A model with no rate must not silently price at zero — that is how an unknown
    cost becomes a confident wrong number."""
    _record(conn, model="gpt-5.6-terra")
    totals = spend.total(conn, "20260825120000")
    assert totals["input_tokens"] == 10_000
    assert totals["unpriced_calls"] == 1


def test_totals_break_down_by_stage(conn):
    _record(conn, stage="analysis", step_id="02")
    _record(conn, stage="screenplay", step_id="03")
    by_stage = spend.by_stage(conn, "20260825120000")
    assert set(by_stage) == {"analysis", "screenplay"}


def test_totals_break_down_by_step(conn):
    _record(conn, stage="analysis", step_id="02")
    _record(conn, stage="analysis", step_id="02")
    _record(conn, stage="analysis", step_id="05")
    steps = spend.by_step(conn, "20260825120000", "analysis")
    assert steps["02"]["calls"] == 2 and steps["05"]["calls"] == 1


def test_a_book_with_no_calls_totals_zero_rather_than_crashing(conn):
    assert spend.total(conn, "20260825120000") == {
        "calls": 0, "input_tokens": 0, "output_tokens": 0,
        "cost_usd": 0.0, "unpriced_calls": 0}


# --- the rate table ----------------------------------------------------------------

def test_rates_come_from_models_yaml_not_from_code():
    """Pricing lives beside the model choice, so switching provider moves both."""
    rates = spend.load_rates()
    assert "gpt-5.6-luna" in rates
    assert rates["gpt-5.6-luna"]["input_per_m"] == 0.20


def test_an_unknown_model_has_no_rate_rather_than_a_default():
    assert spend.rate_for("no-such-model") is None


def test_cost_of_a_priced_call_is_exact():
    assert spend.cost("gpt-5.6-luna", 500_000, 100_000) == pytest.approx(0.22)


def test_cost_of_an_unpriced_call_is_none():
    assert spend.cost("gpt-5.6-terra", 1000, 1000) is None


# --- the gateway records automatically ---------------------------------------------

class _FakeAgent:
    """A caller that spends nothing. No test may call a paid API.

    The gateway CALLS the agent — `agent(prompt, structured_output_model=Model)` — it
    does not use the deprecated `Agent.structured_output()`."""

    def __init__(self, tier):
        self.tier = tier

    def __call__(self, prompt, structured_output_model=None):
        from types import SimpleNamespace
        return SimpleNamespace(
            structured_output=structured_output_model(),
            metrics=SimpleNamespace(accumulated_usage={
                "inputTokens": 1234, "outputTokens": 567, "totalTokens": 1801}))


def test_the_gateway_records_without_the_step_asking(conn, monkeypatch):
    """The failure this removes: a step that forgets `usage={}` recorded nothing, and
    that is exactly why there is no cost history for the analysis run."""
    from pydantic import BaseModel

    from studio import llm

    class Empty(BaseModel):
        pass

    with llm.spend_context(conn, "20260825120000", "analysis", "02"):
        llm.structured("workhorse", "prompt", Empty, _agent=_FakeAgent("workhorse"))

    totals = spend.total(conn, "20260825120000")
    assert totals["calls"] == 1 and totals["input_tokens"] == 1234


def test_calls_outside_a_context_do_not_crash(conn):
    """Recording is best-effort. A missing context must never break a paid call that
    already succeeded — losing the receipt is bad, losing the work is worse."""
    from pydantic import BaseModel

    from studio import llm

    class Empty(BaseModel):
        pass

    assert llm.structured("workhorse", "p", Empty, _agent=_FakeAgent("workhorse")) is not None


def test_the_context_records_the_model_actually_used(conn):
    from pydantic import BaseModel

    from studio import llm

    class Empty(BaseModel):
        pass

    with llm.spend_context(conn, "20260825120000", "screenplay", "03"):
        llm.structured("workhorse", "p", Empty, _agent=_FakeAgent("workhorse"))
    row = conn.execute("SELECT model, tier FROM usage").fetchone()
    assert row["tier"] == "workhorse" and row["model"]
