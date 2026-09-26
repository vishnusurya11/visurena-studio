"""studio.py: the desk from a shell.  `tick` refreshes every book's rows (or
one book's) and prints the counts; `queue` materializes one row and promotes
it, printing its state and what it waits on; `verify` names the disagreements
and resolves nothing; `board` prints v_queue and v_attention as text tables --
the terminal preview of the web board.  Nothing here runs a step or opens the
live database: the test hands it a tmp DB and a tmp library."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from studio import db, episode_home, work_orders

CODEX = "20260901000001"
ROOT = Path(__file__).resolve().parents[1]


def _load_studio_py():
    """The top-level script beside episode.py (the `studio` package shadows its name)."""
    spec = importlib.util.spec_from_file_location("studio_desk", ROOT / "studio.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


studio_py = _load_studio_py()


@pytest.fixture()
def library(tmp_path, monkeypatch):
    root = tmp_path / "library"
    (root / f"{CODEX}_a-book" / "episodes" / "ep04").mkdir(parents=True)
    monkeypatch.setattr(episode_home, "LIBRARY", root)
    monkeypatch.setattr(studio_py, "HOLD", root / "RENDER_HOLD")
    return root


@pytest.fixture()
def conn(tmp_path):
    connection = db.get_connection(tmp_path / "t.db")
    db.init_db(connection)
    db.insert_codex(connection, "Book", codex_id=CODEX)
    return connection


def _out(capsys) -> str:
    return capsys.readouterr().out


def test_tick_prints_its_counts(conn, library, capsys):
    assert studio_py.main(["tick"], conn=conn, library=library) == 0
    assert "materialized=5" in _out(capsys)
    assert studio_py.main(["tick", "--book", CODEX], conn=conn, library=library) == 0
    assert "materialized=0" in _out(capsys)


def test_queue_materializes_one_row_and_says_what_it_waits_on(conn, library, capsys):
    assert studio_py.main(["queue", CODEX, "refs"], conn=conn, library=library) == 0
    assert _out(capsys).strip() == "refs/main blocked analysis/05"
    db.upsert_work_order(conn, CODEX, "analysis", "book", state="done")
    for rel in ("analysis/scenes.json", "analysis/characters/a.json"):
        (library / f"{CODEX}_a-book" / rel).parent.mkdir(parents=True, exist_ok=True)
        (library / f"{CODEX}_a-book" / rel).write_text("{}", encoding="utf-8")
    assert studio_py.main(["queue", CODEX, "refs", "--priority", "2"], conn=conn, library=library) == 0
    assert _out(capsys).strip() == "refs/main queued"
    row = db.work_order(conn, CODEX, "refs", "main")
    assert row["priority"] == 2 and row["source"] == "queue"


def test_queue_needs_a_unit_for_a_chapter_grain_stage(conn, library):
    with pytest.raises(SystemExit, match="unit"):
        studio_py.main(["queue", CODEX, "episode"], conn=conn, library=library)
    assert studio_py.main(["queue", CODEX, "episode", "ep04"], conn=conn, library=library) == 0
    assert db.work_order(conn, CODEX, "episode", "ep04")["state"] == "blocked"


def test_queue_refuses_a_book_the_library_does_not_hold(conn, library):
    with pytest.raises(SystemExit, match="library"):
        studio_py.main(["queue", "20260901000009", "refs"], conn=conn, library=library)


def test_verify_names_the_disagreements_or_says_there_are_none(conn, library, capsys):
    assert studio_py.main(["verify", CODEX, "episode", "ep04"], conn=conn, library=library) == 1
    assert _out(capsys).strip() == "episode/ep04: no row"
    db.upsert_work_order(conn, CODEX, "episode", "ep04", state="queued")
    assert studio_py.main(["verify", CODEX, "episode", "ep04"], conn=conn, library=library) == 0
    assert _out(capsys).strip() == "episode/ep04: rows and disk agree"


def test_board_prints_the_queue_and_the_attention_strip(conn, library, capsys):
    db.upsert_work_order(conn, CODEX, "episode", "ep04", state="queued", priority=3, sequence=4)
    db.upsert_work_order(conn, CODEX, "episode", "ep05", state="failed", step_id="09", blocked_on=None)
    db.upsert_work_order(conn, CODEX, "refs", "main", state="done")
    assert studio_py.main(["board"], conn=conn, library=library) == 0
    out = _out(capsys)
    queue, attention = out.split("NEEDS YOU")
    assert "QUEUE" in queue and "ep04" in queue and "ep05" not in queue
    assert "ep05" in attention and "failed" in attention and "main" not in attention


def test_the_table_lines_up_its_columns():
    rows = [{"stage": "episode", "unit": "ep04", "state": "queued"},
            {"stage": "refs", "unit": "main", "state": "held"}]
    lines = studio_py.table(rows, ("stage", "unit", "state")).splitlines()
    assert lines[0] == "stage    unit  state "
    assert lines[2] == "episode  ep04  queued"
    assert lines[3] == "refs     main  held  "
    assert studio_py.table([], ("stage",)) == "(none)"


def test_a_held_row_shows_on_neither_table(conn, library, capsys):
    db.upsert_work_order(conn, CODEX, "episode", "ep04", state="queued")
    work_orders.hold(conn, "book", "wait", codex_id=CODEX)
    studio_py.main(["tick"], conn=conn, library=library)
    studio_py.main(["board"], conn=conn, library=library)
    assert "ep04" not in _out(capsys)
