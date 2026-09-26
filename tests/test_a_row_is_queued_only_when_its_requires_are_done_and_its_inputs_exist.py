"""The brick's base case (decision 2026-09-25): a row is `queued` when every row
it `requires` (the registry's edge) is `done` and its first step's declared
inputs exist on disk; otherwise `blocked`, with `blocked_on` naming the first
thing it waits for.  Promotion runs both ways (an input that goes takes the row
back to blocked) and never touches a row in any other state.  A hold at the
unit's scope parks a blocked or queued row as `held`; on lift it returns to
`blocked` and the same tick promotes it again -- the pre-hold state is never
stored, because it was never a fact, only a projection."""
from __future__ import annotations

import pytest

from studio import db, episode_home, tick, work_orders

CODEX = "20260901000001"


@pytest.fixture()
def book(tmp_path, monkeypatch):
    root = tmp_path / "library"
    folder = root / f"{CODEX}_a-book"
    (folder / "episodes" / "ep04").mkdir(parents=True)
    monkeypatch.setattr(episode_home, "LIBRARY", root)
    return folder


@pytest.fixture()
def conn(tmp_path):
    connection = db.get_connection(tmp_path / "t.db")
    db.init_db(connection)
    db.insert_codex(connection, "Book", codex_id=CODEX)
    return connection


def _done(conn, stage, unit):
    db.upsert_work_order(conn, CODEX, stage, unit, state="done")


def _inputs(book):
    for rel in ("analysis/scenes.json", "refs/refs.json"):
        (book / rel).parent.mkdir(parents=True, exist_ok=True)
        (book / rel).write_text("{}", encoding="utf-8")


def _state(conn, stage="episode", unit="ep04"):
    row = db.work_order(conn, CODEX, stage, unit)
    return row["state"], row["blocked_on"]


def test_the_required_unit_is_the_same_unit_at_the_same_grain_else_the_book_level_name():
    assert tick.required_unit("refs", "episode", "ep04") == "main"
    assert tick.required_unit("analysis", "episode", "ep04") == "book"
    assert tick.required_unit("episode", "episode", "ep04") == "ep04"
    assert tick.required_unit("analysis", "refs", "main") == "book"


def test_requirements_are_met_only_by_done_rows_and_name_the_first_unmet(conn):
    assert tick.requirements_met(conn, CODEX, "episode", "ep04") == (False, "analysis/06")
    _done(conn, "analysis", "book")
    assert tick.requirements_met(conn, CODEX, "episode", "ep04") == (False, "refs/04")
    db.upsert_work_order(conn, CODEX, "refs", "main", state="running")
    assert tick.requirements_met(conn, CODEX, "episode", "ep04") == (False, "refs/04")
    _done(conn, "refs", "main")
    assert tick.requirements_met(conn, CODEX, "episode", "ep04") == (True, "")
    assert tick.requirements_met(conn, CODEX, "analysis", "book") == (True, "")


def test_only_the_first_steps_inputs_gate_the_queue(book):
    assert tick.first_inputs("episode", "ep04") == ["analysis/scenes.json", "refs/refs.json"]
    assert tick.first_inputs("analysis", "book") == []
    assert tick.missing_inputs(book, "episode", "ep04") == ["analysis/scenes.json", "refs/refs.json"]
    assert tick.inputs_exist(book, "analysis", "book")
    _inputs(book)
    assert tick.inputs_exist(book, "episode", "ep04")
    assert tick.missing_inputs(book, "episode", "ep04") == []


def test_a_row_is_queued_when_its_requires_are_done_and_its_inputs_exist(conn, book):
    tick.materialize(conn, CODEX, "episode", ["ep04"])
    assert tick.promote(conn, CODEX, "episode", "ep04", book) == "blocked"
    assert _state(conn) == ("blocked", "analysis/06")
    _done(conn, "analysis", "book"), _done(conn, "refs", "main")
    assert tick.promote(conn, CODEX, "episode", "ep04", book) == "blocked"
    assert _state(conn) == ("blocked", "in: analysis/scenes.json")
    _inputs(book)
    assert tick.promote(conn, CODEX, "episode", "ep04", book) == "queued"
    assert _state(conn) == ("queued", None)


def test_an_input_that_goes_takes_a_queued_row_back_to_blocked(conn, book):
    tick.materialize(conn, CODEX, "episode", ["ep04"])
    _done(conn, "analysis", "book"), _done(conn, "refs", "main"), _inputs(book)
    assert tick.promote(conn, CODEX, "episode", "ep04", book) == "queued"
    (book / "refs" / "refs.json").unlink()
    assert tick.promote(conn, CODEX, "episode", "ep04", book) == "blocked"
    assert _state(conn) == ("blocked", "in: refs/refs.json")


@pytest.mark.parametrize("state", ["running", "done", "failed", "deferred", "escalated", "held", "stale"])
def test_promote_never_touches_a_row_in_any_other_state(conn, book, state):
    db.upsert_work_order(conn, CODEX, "episode", "ep04", state=state, blocked_on="as it was")
    _done(conn, "analysis", "book"), _done(conn, "refs", "main"), _inputs(book)
    assert tick.promote(conn, CODEX, "episode", "ep04", book) == state
    assert _state(conn) == (state, "as it was")
    assert tick.promote(conn, CODEX, "episode", "ep09", book) == ""


def test_a_hold_parks_a_queued_row_and_a_lift_brings_it_back_through_promote(conn, book):
    tick.materialize(conn, CODEX, "episode", ["ep04"])
    _done(conn, "analysis", "book"), _done(conn, "refs", "main"), _inputs(book)
    tick.tick_stage(conn, CODEX, "episode", book)
    assert _state(conn) == ("queued", None)
    hold_id = work_orders.hold(conn, "book", "re-planning", codex_id=CODEX)
    assert tick.tick_stage(conn, CODEX, "episode", book)["held"] == 1
    row = db.work_order(conn, CODEX, "episode", "ep04")
    assert (row["state"], row["hold_reason"], row["blocked_on"]) == ("held", "re-planning", f"hold {hold_id}")
    work_orders.lift(conn, hold_id)
    tick.tick_stage(conn, CODEX, "episode", book)
    row = db.work_order(conn, CODEX, "episode", "ep04")
    assert (row["state"], row["hold_reason"], row["blocked_on"]) == ("queued", None, None)


def test_a_hold_leaves_a_running_row_running(conn, book):
    db.upsert_work_order(conn, CODEX, "episode", "ep04", state="running")
    work_orders.hold(conn, "unit", "look again", codex_id=CODEX, stage="episode", unit="ep04")
    assert tick.park_held(conn, CODEX, "episode", "ep04") == "running"
    assert tick.release_held(conn, CODEX, "episode", "ep04") == "running"
    assert tick.park_held(conn, CODEX, "episode", "ep05") == ""


def test_the_render_hold_file_reaches_the_rows_through_the_studio_hold(conn, book, tmp_path):
    tick.materialize(conn, CODEX, "episode", ["ep04"])
    _done(conn, "analysis", "book"), _done(conn, "refs", "main"), _inputs(book)
    hold_path = tmp_path / "RENDER_HOLD"
    hold_path.write_text("owner", encoding="utf-8")
    counts = tick.tick(conn, book.parent, hold_path=hold_path)
    assert counts["holds"] == 1 and _state(conn)[0] == "held"
    hold_path.unlink()
    counts = tick.tick(conn, book.parent, hold_path=hold_path)
    assert counts["holds"] == 0 and _state(conn) == ("queued", None)
