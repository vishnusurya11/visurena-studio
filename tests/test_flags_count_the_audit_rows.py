"""`flagged` is a COUNT on a done row, not a state (decision 2026-09-25,
"States"): `work_orders.flags` is the number of audit rows the unit has -- one
per terminal rung -- refreshed on every completed event.  A book with no
library folder (a test's, a book-level stage with no home) reads nothing and
never raises inside add_event."""
from __future__ import annotations

import pytest

from studio import audit_rows, db, episode_home, verdict_rows

CODEX = "20260901000001"


@pytest.fixture()
def library(tmp_path, monkeypatch):
    folder = tmp_path / "library"
    folder.mkdir()
    monkeypatch.setattr(episode_home, "LIBRARY", folder)
    return folder


@pytest.fixture()
def book(library):
    folder = library / f"{CODEX}_a-book"
    folder.mkdir()
    return folder


@pytest.fixture()
def conn(tmp_path):
    connection = db.get_connection(tmp_path / "t.db")
    db.init_db(connection)
    db.insert_codex(connection, "Book", codex_id=CODEX)
    return connection


def _flag(book, unit, gate="EYE_PANELS"):
    audit_rows.append(book, {"unit": unit, "gate": gate, "judge": "judge:panel_eye@1",
                             "terminal": "keep_best"})


def _complete(conn, step="03", unit="ep04"):
    db.add_event(conn, CODEX, "episode", step, "started", run_id="r1", unit=unit)
    db.add_event(conn, CODEX, "episode", step, "completed", run_id="r1", unit=unit)
    return db.work_order(conn, CODEX, "episode", unit)


def test_two_audit_rows_for_the_unit_are_two_flags(conn, book):
    _flag(book, "ep04")
    _flag(book, "ep04", "EYE_TAKES")
    _flag(book, "ep05")
    assert _complete(conn)["flags"] == 2
    assert _complete(conn, unit="ep05")["flags"] == 1


def test_no_audit_rows_is_zero_flags(conn, book):
    assert _complete(conn)["flags"] == 0
    assert verdict_rows.flags(book, "ep04") == 0


def test_a_book_with_no_library_folder_never_raises(conn, library):
    row = _complete(conn)
    assert row["flags"] == 0 and row["verdicts"] is None and row["state"] == "running"
    assert db._book_dir(CODEX) is None


def test_a_library_that_does_not_exist_never_raises(conn, tmp_path, monkeypatch):
    monkeypatch.setattr(episode_home, "LIBRARY", tmp_path / "nowhere")
    assert _complete(conn)["flags"] == 0


def test_a_sheet_that_will_not_read_is_zero_flags_not_a_failed_event(conn, book):
    target = audit_rows.path(book)
    target.parent.mkdir()
    target.write_text("not a row\n", encoding="utf-8")
    assert _complete(conn)["flags"] == 0


def test_a_row_the_step_did_not_complete_keeps_its_flags(conn, book):
    _flag(book, "ep04")
    assert _complete(conn)["flags"] == 1
    db.add_event(conn, CODEX, "episode", "04", "failed", run_id="r1", unit="ep04")
    assert db.work_order(conn, CODEX, "episode", "ep04")["flags"] == 1
