"""The tick (decision 2026-09-25, "How a department is driven"): rows from the
registry x the slate, INSERT OR IGNORE.  The slate is what a stage has on disk
today -- every `episodes/epNN` folder for the chapter-grain line, the book-level
unit name for every other department (`main` for refs, `book` for the rest,
the way each runner names its unit in events).  A row is born `blocked` with
`source='queue'` and its number, sequence, home and kind from the unit grammar;
a second tick makes nothing twice; a book the library does not hold gets no
row.  Every runner's first act (the Tracker's start) is this tick for its own
book, and it never raises into a run."""
from __future__ import annotations

import pytest

from studio import db, episode_home, tick, tracking

CODEX = "20260901000001"
OTHER = "20260901000002"


@pytest.fixture()
def library(tmp_path, monkeypatch):
    root = tmp_path / "library"
    (root / f"{CODEX}_a-book" / "episodes" / "ep01").mkdir(parents=True)
    (root / f"{CODEX}_a-book" / "episodes" / "ep03").mkdir(parents=True)
    (root / f"{CODEX}_a-book" / "episodes" / "ep01_short").mkdir(parents=True)
    monkeypatch.setattr(episode_home, "LIBRARY", root)
    return root


@pytest.fixture()
def book(library):
    return library / f"{CODEX}_a-book"


@pytest.fixture()
def conn(tmp_path):
    connection = db.get_connection(tmp_path / "t.db")
    db.init_db(connection)
    db.insert_codex(connection, "Book", codex_id=CODEX)
    db.insert_codex(connection, "Other, not in the library", codex_id=OTHER)
    return connection


def test_the_slate_is_the_folders_for_the_chapter_line_and_a_name_for_the_rest(book):
    assert tick.slate(CODEX, "episode", book) == ["ep01", "ep03"]
    assert tick.slate(CODEX, "refs", book) == ["main"]
    assert tick.slate(CODEX, "analysis", book) == ["book"]
    assert tick.slate(CODEX, "trailer", book) == ["book"]
    assert tick.slate(CODEX, "episode", book / "nowhere") == []


def test_the_unit_grammar_gives_number_sequence_home_and_kind():
    assert tick.unit_grammar("episode", "ep04") == {
        "home": "episodes/ep04", "kind": "chapter", "number": 4, "sequence": 4}
    assert tick.unit_grammar("refs", "main") == {"home": "refs", "kind": "book"}
    assert tick.unit_grammar("analysis", "book") == {"home": "analysis", "kind": "book"}


def test_materialize_makes_one_blocked_queue_row_per_unit_and_never_twice(conn):
    assert tick.materialize(conn, CODEX, "episode", ["ep01", "ep03"]) == 2
    row = db.work_order(conn, CODEX, "episode", "ep03")
    assert (row["state"], row["source"], row["number"], row["sequence"]) == ("blocked", "queue", 3, 3)
    assert (row["home"], row["kind"]) == ("episodes/ep03", "chapter") and row["requested_at"]
    assert tick.materialize(conn, CODEX, "episode", ["ep01", "ep03"]) == 0
    assert tick.materialize(conn, CODEX, "episode", []) == 0


def test_materialize_leaves_a_row_a_run_already_wrote_as_it_is(conn):
    db.add_event(conn, CODEX, "episode", "02", "started", run_id="r1", unit="ep01")
    assert tick.materialize(conn, CODEX, "episode", ["ep01"]) == 0
    row = db.work_order(conn, CODEX, "episode", "ep01")
    assert row["state"] == "running" and row["source"] == "run"


def test_a_tick_materializes_every_registered_stage_of_every_book_in_the_library(conn, library):
    counts = tick.tick(conn, library, hold_path=library / "RENDER_HOLD")
    assert counts["materialized"] == 2 + 4          # ep01, ep03 + refs, analysis, screenplay, trailer
    assert [r["unit"] for r in db.department_rows(conn, "episode")] == ["ep01", "ep03"]
    assert db.work_order(conn, CODEX, "refs", "main")["home"] == "refs"
    assert db.work_order(conn, OTHER, "refs", "main") is None
    assert tick.tick(conn, library, hold_path=library / "RENDER_HOLD")["materialized"] == 0


def test_a_tick_can_be_asked_for_one_book(conn, library):
    assert tick.tick(conn, library, codex_ids=[OTHER], hold_path=library / "RENDER_HOLD")["materialized"] == 0
    assert tick.tick(conn, library, codex_ids=[CODEX], hold_path=library / "RENDER_HOLD")["materialized"] == 6


def test_book_folder_finds_the_folder_by_its_id_prefix(library):
    assert tick.book_folder(library, CODEX) == library / f"{CODEX}_a-book"
    assert tick.book_folder(library, OTHER) is None
    assert tick.book_folder(library / "nowhere", CODEX) is None


def test_registered_is_every_codex_row_in_id_order(conn):
    assert tick.registered(conn) == [CODEX, OTHER]


def test_tick_book_refreshes_one_books_rows_and_skips_a_book_it_cannot_find(conn, library):
    assert tick.tick_book(conn, CODEX)["materialized"] == 6
    assert tick.tick_book(conn, OTHER) is None                 # no library folder
    assert tick.tick_book(conn, "20260901000009") is None      # no codex row either
    assert tick.tick_book(conn, f"{CODEX}_a-book")["materialized"] == 0   # a folder name keys the same book


def test_tick_book_never_raises_into_a_run(conn, library, monkeypatch, caplog):
    def boom(*a, **k):
        raise RuntimeError("the desk is on fire")
    monkeypatch.setattr(tick, "tick_stage", boom)
    assert tick.tick_book(conn, CODEX) is None
    assert "the desk is on fire" in caplog.text


def test_a_trackers_start_ticks_its_book(conn, library, tmp_path):
    tracking.Tracker(conn, CODEX, "episode", logs_root=tmp_path / "logs", unit="ep01")
    assert [r["unit"] for r in db.department_rows(conn, "episode")] == ["ep01", "ep03"]
    tracking.Tracker(conn, "20260901000009", "episode", logs_root=tmp_path / "logs")   # unknown: no stop
