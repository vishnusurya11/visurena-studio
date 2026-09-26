"""C8: `scripts/audit/backfill_work_orders.py` prints the listing and writes
nothing unless --write; --book narrows to one codex; --with-publish adds the
publish rows; --force lets the ambiguous rows through.  The default
connection is read-only (the live DB belongs to whatever run is on it)."""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.audit import backfill_work_orders as cli  # noqa: E402
from studio import db, episode_home  # noqa: E402

CODEX = "20260901000001"
OTHER = "20260901000002"


@pytest.fixture()
def library(tmp_path, monkeypatch):
    folder = tmp_path / "library"
    folder.mkdir()
    monkeypatch.setattr(episode_home, "LIBRARY", folder)
    for codex in (CODEX, OTHER):
        home = folder / f"{codex}_a-book" / "episodes" / "ep01"
        episode_home.write_json(home / "plan.json", {"number": 1})
        (home / "cut").mkdir()
        (home / "cut" / "master_r2v.mp4").write_bytes(b"m")
        episode_home.write_json(home / "qc_r2v.json", {"passed": True})
        episode_home.write_json(home / "youtube.json", {})
        (folder / f"{codex}_a-book" / "uploads.jsonl").write_text(
            json.dumps({"episode": 1, "video_id": "v", "sha8": "aa11bb22", "privacy": "public"}) + "\n",
            encoding="utf-8")
    return folder


@pytest.fixture()
def conn(tmp_path):
    connection = db.get_connection(tmp_path / "t.db")
    db.init_db(connection)
    for codex in (CODEX, OTHER):
        db.insert_codex(connection, "Book", codex_id=codex)
    return connection


def _count(conn):
    return conn.execute("SELECT COUNT(*) FROM work_orders").fetchone()[0]


def test_the_default_is_a_dry_run_that_prints_the_listing(conn, library, capsys):
    assert cli.main(["backfill_work_orders.py"], conn=conn, library=library) == 0
    out = capsys.readouterr().out
    assert "rows: 2  derivable: 2" in out and "dry run: nothing written" in out
    assert _count(conn) == 0


def test_write_upserts_the_rows_and_book_narrows_to_one(conn, library, capsys):
    cli.main(["backfill_work_orders.py", "--book", OTHER, "--write"], conn=conn, library=library)
    assert "wrote 1 rows" in capsys.readouterr().out
    assert _count(conn) == 1 and db.work_order(conn, OTHER, "episode", "ep01")["source"] == "backfill"
    cli.main(["backfill_work_orders.py", f"--book={CODEX}_a-book", "--write"], conn=conn, library=library)
    assert _count(conn) == 2


def test_with_publish_adds_the_publish_rows(conn, library, capsys):
    cli.main(["backfill_work_orders.py", "--with-publish"], conn=conn, library=library)
    out = capsys.readouterr().out
    assert out.count("aa11bb22@youtube") == 2 and "not in the registry" in out
    cli.main(["backfill_work_orders.py", "--with-publish", "--write"], conn=conn, library=library)
    assert _count(conn) == 4


def test_force_writes_the_ambiguous_rows_too(conn, library, capsys):
    (library / f"{CODEX}_a-book" / "episodes" / "ep01" / "qc_r2v.json").unlink()
    cli.main(["backfill_work_orders.py", "--write"], conn=conn, library=library)
    assert "wrote 1 rows" in capsys.readouterr().out
    cli.main(["backfill_work_orders.py", "--write", "--force"], conn=conn, library=library)
    assert "wrote 2 rows" in capsys.readouterr().out


def test_options_are_read_off_argv():
    got = cli.options(["x", "--book", CODEX, "--write", "--force", "--with-publish"])
    assert got == {"books": [CODEX], "write": True, "force": True, "with_publish": True}
    assert cli.options(["x"]) == {"books": None, "write": False, "force": False, "with_publish": False}
    assert cli.options(["x", f"--book={OTHER}_a-book"])["books"] == [OTHER]


def test_the_default_connection_is_read_only(tmp_path):
    path = tmp_path / "ro.db"
    seed = db.get_connection(path)
    db.init_db(seed)
    seed.close()
    conn = cli.open_readonly(path)
    assert conn.execute("SELECT COUNT(*) FROM codex").fetchone()[0] == 0
    with pytest.raises(sqlite3.OperationalError):
        conn.execute("INSERT INTO codex (id, name, updated_at) VALUES ('20260901000009', 'x', 'now')")
