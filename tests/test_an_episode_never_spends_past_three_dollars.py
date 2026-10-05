"""Owner 2026-10-04: "target 3 dollar max for episode generation".  ep14-16
spent $2.69-4.11 on the plan step alone, through 120-169 writer calls that
nothing stopped.  Every paid request passes `_NativeStructuredCaller`, so the
wall sits there: before a request, the episode's recorded spend plus this
call's estimated cost must stay under the ceiling in models.yaml, or the call
is refused BEFORE it is sent (OverBudget).  A call outside an episode (no unit
in the spend context) is not walled here.  $0: an in-memory database."""
from __future__ import annotations

import sqlite3

import pytest

from studio import llm, spend


@pytest.fixture()
def conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    spend.init(c)
    return c


def charge(conn, usd, unit="ep17"):
    conn.execute("INSERT INTO usage (recorded_at, codex_id, stage, step_id, tier, model,"
                 " input_tokens, output_tokens, cost_usd, unit) VALUES"
                 " ('t','book','episode','02','local','gpt-5.6-luna',0,0,?,?)", (usd, unit))


def test_unit_spent_sums_one_episode_only(conn):
    charge(conn, 1.25); charge(conn, 0.50); charge(conn, 9.00, unit="ep16")
    assert spend.unit_spent(conn, "book", "ep17") == pytest.approx(1.75)


def test_a_call_that_would_cross_the_ceiling_is_refused_before_it_is_sent(conn):
    charge(conn, 2.99)               # + this call (~$0.03) crosses $3.00
    with llm.spend_context(conn, "book", "episode", "02", unit="ep17"):
        with pytest.raises(llm.OverBudget, match="ep17"):
            llm.guard_spend(model="gpt-5.6-luna", prompt="x" * 200_000, ceiling=3.00)


def test_a_call_well_under_the_ceiling_passes(conn):
    charge(conn, 0.10)
    with llm.spend_context(conn, "book", "episode", "02", unit="ep17"):
        llm.guard_spend(model="gpt-5.6-luna", prompt="x" * 200_000, ceiling=3.00)


def test_a_call_outside_an_episode_is_not_walled(conn):
    charge(conn, 50.0, unit=None)
    with llm.spend_context(conn, "book", "screenplay", "01"):
        llm.guard_spend(model="gpt-5.6-luna", prompt="x" * 200_000, ceiling=3.00)


def test_the_ceiling_comes_from_models_yaml():
    assert llm.episode_ceiling_usd() == pytest.approx(3.00)
