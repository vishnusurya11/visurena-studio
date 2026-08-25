"""The screenplay stage runner — a sibling of analysis.py, not a step inside it.

The one behaviour that distinguishes it: analysis may run on any book, but screenplay
may only run on a book whose analysis has COMPLETED. A screenplay built from a
half-finished dossier would be grounded in nothing.
"""

from __future__ import annotations

import pytest

import screenplay
from studio import db


@pytest.fixture()
def conn(tmp_path):
    connection = db.get_connection(tmp_path / "test.db")
    db.init_db(connection)
    return connection


def _book(connection, name: str, codex_id: str) -> str:
    return db.insert_codex(connection, name, codex_id=codex_id)


def _finish_analysis(connection, codex_id: str) -> None:
    db.add_event(connection, codex_id, "analysis", "06", "completed")


# --- the gate: analysis must be complete first -------------------------------------

def test_book_without_analysis_is_not_ready(conn):
    _book(conn, "Unanalysed", "20260825000001")
    assert db.codex_ready_for_stage(conn, "screenplay", "05", "analysis", "06") == []


def test_book_with_completed_analysis_is_ready(conn):
    codex_id = _book(conn, "Analysed", "20260825000002")
    _finish_analysis(conn, codex_id)
    assert db.codex_ready_for_stage(conn, "screenplay", "05", "analysis", "06") == [codex_id]


def test_partial_analysis_is_not_ready(conn):
    """Steps 01-05 done, 06 not. The stage is not complete, so screenplay must wait."""
    codex_id = _book(conn, "Partial", "20260825000003")
    for step in ("01", "02", "03", "04", "05"):
        db.add_event(conn, codex_id, "analysis", step, "completed")
    assert db.codex_ready_for_stage(conn, "screenplay", "05", "analysis", "06") == []


def test_book_with_completed_screenplay_is_not_ready(conn):
    codex_id = _book(conn, "Done", "20260825000004")
    _finish_analysis(conn, codex_id)
    db.add_event(conn, codex_id, "screenplay", "05", "completed")
    assert db.codex_ready_for_stage(conn, "screenplay", "05", "analysis", "06") == []


def test_ready_books_come_back_in_id_order(conn):
    second = _book(conn, "B", "20260825000006")
    first = _book(conn, "A", "20260825000005")
    for codex_id in (first, second):
        _finish_analysis(conn, codex_id)
    ready = db.codex_ready_for_stage(conn, "screenplay", "05", "analysis", "06")
    assert ready == [first, second]


# --- the stage is registered -------------------------------------------------------

def test_screenplay_stage_has_summary_columns(conn):
    codex_id = _book(conn, "Marked", "20260825000007")
    db.mark_stage(conn, codex_id, "screenplay", "running")
    assert db.get_codex(conn, codex_id)["screenplay_status"] == "running"


# --- the registry drives the pipeline shape ----------------------------------------

def test_registry_lists_five_steps_in_order():
    ids = [entry["id"] for entry in screenplay.load_registry()["steps"]]
    assert ids == ["01", "02", "03", "04", "05"]


def test_steps_are_loaded_lazily_up_to_the_limit():
    """Only steps we intend to run get imported, so an unbuilt step 02 cannot break
    the runner. This is the one place screenplay.py deliberately differs from
    analysis.py, whose steps all exist."""
    steps = screenplay.load_steps(run_until="01")
    assert [step.STEP_ID for step in steps] == ["01"]


def test_loaded_step_id_must_match_the_registry():
    step = screenplay.load_steps(run_until="01")[0]
    assert step.STEP_ID == "01" and step.NAME == "dossier"


# --- step-level events: the completion signal the whole gate rests on --------------

class _FakeStep:
    """A step module that records it ran, without touching a library folder."""

    def __init__(self, step_id: str, name: str, explode: bool = False):
        self.STEP_ID, self.NAME, self.explode, self.ran = step_id, name, explode, False

    def run(self, codex_id: str) -> None:
        self.ran = True
        if self.explode:
            raise RuntimeError("step failed")


def _events(connection, codex_id: str, step_id: str) -> list[str]:
    rows = connection.execute(
        "SELECT event FROM events WHERE codex_id = ? AND stage = 'screenplay'"
        " AND step_id = ? ORDER BY event_ts", (codex_id, step_id))
    return [row["event"] for row in rows]


def test_process_emits_a_step_level_completed_event(conn, monkeypatch):
    """Steps only ever wrote SUBSTEP events (01_01, 01_02 ...). Nothing wrote '01', so
    codex_pending_stage / codex_ready_for_stage — which key on the step id — could never
    match, and every book stayed pending forever. The runner owns this event."""
    codex_id = _book(conn, "Stepwise", "20260825000010")
    step = _FakeStep("01", "dossier")
    monkeypatch.setattr(screenplay, "load_steps", lambda *a, **k: [step])
    screenplay.process(conn, codex_id)
    assert step.ran
    assert _events(conn, codex_id, "01") == ["started", "completed"]


def test_a_failed_step_records_failed_and_reraises(conn, monkeypatch):
    codex_id = _book(conn, "Broken", "20260825000011")
    monkeypatch.setattr(screenplay, "load_steps",
                        lambda *a, **k: [_FakeStep("01", "dossier", explode=True)])
    with pytest.raises(RuntimeError):
        screenplay.process(conn, codex_id)
    assert _events(conn, codex_id, "01") == ["started", "failed"]
    assert db.get_codex(conn, codex_id)["screenplay_status"] == "failed"


def test_a_partial_run_leaves_the_stage_running_not_completed(conn, monkeypatch):
    """RUN_UNTIL_STEP stops early on purpose. 'running' means in progress, and the
    stage must not claim completion it did not reach."""
    codex_id = _book(conn, "Partial run", "20260825000012")
    monkeypatch.setattr(screenplay, "load_steps",
                        lambda *a, **k: [_FakeStep("01", "dossier")])
    screenplay.process(conn, codex_id)
    assert db.get_codex(conn, codex_id)["screenplay_status"] == "running"


def test_completing_the_final_step_completes_the_stage(conn, monkeypatch):
    codex_id = _book(conn, "Full run", "20260825000013")
    monkeypatch.setattr(screenplay, "load_steps",
                        lambda *a, **k: [_FakeStep("05", "verify")])
    monkeypatch.setattr(screenplay, "RUN_UNTIL_STEP", "05")
    screenplay.process(conn, codex_id)
    assert db.get_codex(conn, codex_id)["screenplay_status"] == "completed"
    assert db.codex_ready_for_stage(conn, "screenplay", "05", "analysis", "06") == []
