"""Fleet C A2 (2026-10-22): every LLM spend row carries its seconds and output tokens per second.

The writer step ran 37-206 min and the usage table held tokens only, so nothing split it into
calls, rate and loops.  The gateway times each model call (a refused reply too: it was paid for
and it took time) and spend.record keeps `duration_s` and `out_tok_s`.  No paid API is called."""
from __future__ import annotations

from types import SimpleNamespace

import pytest
from pydantic import BaseModel

from studio import db, llm, spend

CODEX = "20260825120000"


@pytest.fixture()
def conn(tmp_path):
    connection = db.get_connection(tmp_path / "spend.db")
    db.init_db(connection)
    db.insert_codex(connection, "Test Book", codex_id=CODEX)
    return connection


class Empty(BaseModel):
    pass


class TwelveSecondAgent:
    """A caller that takes 12 s on the fake clock and spends nothing."""

    def __init__(self, clock: dict, refuse_first: bool = False):
        self.clock, self.refuse_first = clock, refuse_first

    def __call__(self, prompt, structured_output_model=None):
        self.clock["now"] += 12.0
        if self.refuse_first:
            self.refuse_first = False
            refused = llm.StructuredOutputException("cut off")
            refused.usage = {"input_tokens": 100, "output_tokens": 240}
            raise refused
        return SimpleNamespace(structured_output=structured_output_model(), metrics=SimpleNamespace(
            accumulated_usage={"inputTokens": 1000, "outputTokens": 600, "totalTokens": 1600}))


def _fake_clock(monkeypatch) -> dict:
    clock = {"now": 5000.0}
    monkeypatch.setattr(llm, "_clock", lambda: clock["now"])
    return clock


def test_a_12_second_call_writes_its_seconds_and_rate(conn, monkeypatch):
    clock = _fake_clock(monkeypatch)
    with llm.spend_context(conn, CODEX, "episode", "02"):
        llm.structured("workhorse", "p", Empty, _agent=TwelveSecondAgent(clock))
    row = conn.execute("SELECT duration_s, out_tok_s FROM usage").fetchone()
    assert row["duration_s"] == pytest.approx(12.0) and row["out_tok_s"] == pytest.approx(50.0)


def test_a_refused_reply_is_timed_on_its_own_row(conn, monkeypatch):
    clock = _fake_clock(monkeypatch)
    with llm.spend_context(conn, CODEX, "episode", "02"):
        llm.structured("workhorse", "p", Empty, _agent=TwelveSecondAgent(clock, refuse_first=True))
    rows = conn.execute("SELECT output_tokens, duration_s, out_tok_s FROM usage ORDER BY id").fetchall()
    assert [(r["output_tokens"], r["duration_s"], r["out_tok_s"]) for r in rows] == [(240, 12.0, 20.0),
                                                                                     (600, 12.0, 50.0)]


def test_a_row_with_no_seconds_keeps_both_null(conn):
    spend.record(conn, CODEX, "episode", "02", "workhorse", "gpt-5.6-luna", 10, 20)
    row = conn.execute("SELECT duration_s, out_tok_s FROM usage").fetchone()
    assert row["duration_s"] is None and row["out_tok_s"] is None
