"""C5 (decision 2026-09-25, the Command Center): a unit's paid cost is answerable.

`usage` rows carry the unit the spend context was opened for -- NULL for a
book-level stage -- and the step the journal last started, so a runner that
opens ONE context around its steps attributes every call to the right step
with no cooperation from the step.  `db.unit_cost` sums a unit's rows and is
None while any of them is unpriced (an unknown cost never becomes $0.00).
`db.link_usage_to_orders` backfills `usage.order_id` from the work-order row.

No test calls a paid API: the agent is always faked.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest
from pydantic import BaseModel

from studio import db, llm, spend, tracking

CODEX = "20260901000001"


class Empty(BaseModel):
    pass


class _FakeAgent:
    """Spends nothing; answers with a fixed token count."""

    def __call__(self, prompt, structured_output_model=None):
        return SimpleNamespace(
            structured_output=structured_output_model(),
            metrics=SimpleNamespace(accumulated_usage={
                "inputTokens": 100, "outputTokens": 10, "totalTokens": 110}))


def _call():
    llm.structured("workhorse", "p", Empty, _agent=_FakeAgent())


@pytest.fixture()
def conn(tmp_path):
    connection = db.get_connection(tmp_path / "t.db")
    db.init_db(connection)
    db.insert_codex(connection, "Book", codex_id=CODEX)
    return connection


def _usage(conn) -> list:
    return [dict(r) for r in conn.execute("SELECT * FROM usage ORDER BY id")]


# --- the context tags the unit ---------------------------------------------------


def test_a_row_written_inside_a_unit_scoped_context_carries_the_unit(conn):
    with llm.spend_context(conn, CODEX, "episode", "02", unit="ep04"):
        _call()
    assert [r["unit"] for r in _usage(conn)] == ["ep04"]


def test_a_row_written_in_a_book_level_context_carries_null(conn):
    with llm.spend_context(conn, CODEX, "analysis", "02"):
        _call()
    assert [r["unit"] for r in _usage(conn)] == [None]


def test_the_unit_is_restored_when_a_nested_context_closes(conn):
    with llm.spend_context(conn, CODEX, "episode", "02", unit="ep04"):
        with llm.spend_context(conn, CODEX, "episode", "02"):
            _call()
        _call()
    assert [r["unit"] for r in _usage(conn)] == [None, "ep04"]


def test_spend_record_takes_a_unit(conn):
    spend.record(conn, CODEX, "episode", "02", "workhorse", "gpt-5.6-luna", 1, 1, unit="ep01")
    assert _usage(conn)[0]["unit"] == "ep01"


# --- a runner-level context follows the journal ----------------------------------


def test_a_context_opened_without_a_step_follows_the_journals_started(conn, tmp_path):
    """episode.py opens ONE context around run_steps; every `started` the
    tracker journals moves the step the next call is attributed to."""
    tracker = tracking.Tracker(conn, CODEX, "episode", logs_root=tmp_path, unit="ep01")
    with llm.spend_context(conn, CODEX, "episode", None, unit="ep01"):
        tracker.event("01", "started")
        _call()
        tracker.event("02", "started")
        _call()
    assert [(r["step_id"], r["unit"]) for r in _usage(conn)] == [("01", "ep01"), ("02", "ep01")]


def test_a_context_opened_with_a_step_is_pinned(conn, tmp_path):
    """analysis, screenplay and trailer pin the step themselves; a substep the
    step journals (01_01) must not re-attribute the step's calls."""
    tracker = tracking.Tracker(conn, CODEX, "analysis", logs_root=tmp_path)
    with llm.spend_context(conn, CODEX, "analysis", "01"):
        tracker.event("01_01", "started")
        _call()
    assert [r["step_id"] for r in _usage(conn)] == ["01"]


def test_spend_step_outside_a_context_is_a_no_op():
    llm.spend_step("07")
    assert llm._SPEND == {}


# --- the runners open one ---------------------------------------------------------


def _opts(tmp_path):
    return dict(logs_root=tmp_path / "logs", busy=lambda: False, hold=tmp_path / "RENDER_HOLD",
                launch=lambda cmd: 0)


def test_episode_process_attributes_a_steps_call_to_its_unit_and_step(conn, tmp_path, monkeypatch):
    import episode
    from studio import episode_home, step_runner
    monkeypatch.setattr(episode_home, "book_dir", lambda codex_id: tmp_path / "book")
    (tmp_path / "book").mkdir()
    steps = step_runner.load_steps("episode")
    for step in steps:
        monkeypatch.setattr(step, "done", lambda ctx: True)
    monkeypatch.setattr(steps[1], "done", lambda ctx: False)
    monkeypatch.setattr(steps[1], "run", lambda ctx: _call())
    assert episode.process(conn, CODEX, 3, [], **_opts(tmp_path)) == "completed"
    assert [(r["stage"], r["step_id"], r["unit"]) for r in _usage(conn)] == [("episode", "02", "ep03")]


def test_refs_process_attributes_a_steps_call_to_unit_main(conn, tmp_path, monkeypatch):
    import refs
    from studio import refs_run, step_runner
    book = tmp_path / "book"
    (book / "refs").mkdir(parents=True)
    monkeypatch.setattr(refs_run.episode_home, "book_dir", lambda codex_id: book)
    steps = step_runner.load_steps("refs")
    for step in steps:
        monkeypatch.setattr(step, "done", lambda ctx: True)
    monkeypatch.setattr(steps[0], "done", lambda ctx: False)
    monkeypatch.setattr(steps[0], "run", lambda ctx: _call())
    assert refs.process(conn, CODEX, [], **_opts(tmp_path)) == "completed"
    assert [(r["stage"], r["step_id"], r["unit"]) for r in _usage(conn)] == [("refs", "01", "main")]


# --- db.unit_cost / db.unit_usage -------------------------------------------------


def _row(conn, unit, model="gpt-5.6-luna", stage="episode"):
    spend.record(conn, CODEX, stage, "02", "workhorse", model, 1_000_000, 0, unit=unit)


def test_unit_cost_sums_the_units_priced_rows_only(conn):
    _row(conn, "ep01")
    _row(conn, "ep01")
    _row(conn, "ep02")
    assert db.unit_cost(conn, CODEX, "episode", "ep01") == pytest.approx(0.40)


def test_unit_cost_is_none_while_an_unpriced_call_exists(conn):
    _row(conn, "ep01")
    _row(conn, "ep01", model="gpt-5.6-terra")
    assert db.unit_cost(conn, CODEX, "episode", "ep01") is None


def test_a_unit_with_no_calls_costs_zero(conn):
    assert db.unit_cost(conn, CODEX, "episode", "ep09") == 0.0


def test_a_book_level_stage_answers_to_the_unit_book(conn):
    _row(conn, None, stage="analysis")
    assert db.unit_cost(conn, CODEX, "analysis", "book") == pytest.approx(0.20)
    assert len(db.unit_usage(conn, CODEX, "analysis", "book")) == 1


def test_unit_usage_lists_the_units_rows_in_order(conn):
    _row(conn, "ep01")
    _row(conn, "ep02")
    _row(conn, "ep01")
    rows = db.unit_usage(conn, CODEX, "episode", "ep01")
    assert [r["id"] for r in rows] == [1, 3] and all(r["unit"] == "ep01" for r in rows)


# --- usage.order_id backfill ------------------------------------------------------


def test_link_usage_to_orders_sets_order_id_from_the_units_row(conn):
    _row(conn, "ep01")
    _row(conn, None, stage="analysis")
    _row(conn, "ep07")                                     # no order row yet
    ep = db.upsert_work_order(conn, CODEX, "episode", "ep01", state="queued")
    book = db.upsert_work_order(conn, CODEX, "analysis", "book", state="queued")
    assert db.link_usage_to_orders(conn) == 2
    assert [r["order_id"] for r in _usage(conn)] == [ep, book, None]


def test_link_usage_to_orders_is_idempotent_and_never_relinks(conn):
    _row(conn, "ep01")
    first = db.upsert_work_order(conn, CODEX, "episode", "ep01", state="queued")
    assert db.link_usage_to_orders(conn) == 1
    assert db.link_usage_to_orders(conn) == 0
    assert _usage(conn)[0]["order_id"] == first
