"""studio_cli.py: the owner's hand from a shell.  Every subcommand is one row
(a hold, a lift, an order) and prints its id; nothing here runs a step,
touches the library or opens the live database (`queue` belongs to the tick)."""
from __future__ import annotations

import pytest

import studio_cli
from studio import casebook, db, episode_home, work_orders

CODEX = "20260901000001"


@pytest.fixture()
def conn(tmp_path):
    connection = db.get_connection(tmp_path / "t.db")
    db.init_db(connection)
    db.insert_codex(connection, "Book", codex_id=CODEX)
    return connection


@pytest.fixture()
def book(tmp_path, monkeypatch):
    home = tmp_path / "book"
    (home / "episodes" / "ep04").mkdir(parents=True)
    (home / "episodes" / "ep04" / "plan.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(episode_home, "book_dir", lambda _id: home)
    return home


def _printed(capsys) -> int:
    return int(capsys.readouterr().out.strip().splitlines()[-1])


def test_hold_and_lift(conn, capsys):
    assert studio_cli.main(["hold", "book", "--book", CODEX, "--reason", "re-planning"], conn=conn) == 0
    hold_id = _printed(capsys)
    (row,) = work_orders.active_holds(conn, CODEX, "episode", "ep04")
    assert row["id"] == hold_id and row["reason"] == "re-planning"
    assert studio_cli.main(["lift", str(hold_id)], conn=conn) == 0
    assert _printed(capsys) == 2
    assert work_orders.active_holds(conn) == []


def test_a_studio_hold_and_a_unit_hold(conn, capsys):
    studio_cli.main(["hold", "studio", "--reason", "power"], conn=conn)
    studio_cli.main(["hold", "unit", "--book", CODEX, "--stage", "episode", "--unit", "ep04",
                     "--reason", "look again"], conn=conn)
    assert [h["scope"] for h in work_orders.active_holds(conn, CODEX, "episode", "ep04")] == ["studio", "unit"]


def test_a_hold_whose_scope_names_no_book_is_refused(conn):
    with pytest.raises(SystemExit, match="codex_id"):
        studio_cli.main(["hold", "book", "--reason", "nothing named"], conn=conn)


@pytest.mark.parametrize("kind", ["bump", "retry", "requeue"])
def test_a_unit_order_is_one_orders_row(conn, capsys, kind):
    assert studio_cli.main([kind, CODEX, "episode", "ep04"], conn=conn) == 0
    order_id = _printed(capsys)
    (row,) = work_orders.pending_orders(conn, CODEX, "episode", "ep04")
    assert row["id"] == order_id and row["kind"] == kind and row["scope"] == "unit" and row["taken_ts"] is None


def test_a_library_folder_name_is_keyed_by_its_id(conn):
    studio_cli.main(["bump", CODEX + "_a-book-slug", "episode", "ep04"], conn=conn)
    assert len(work_orders.pending_orders(conn, CODEX, "episode", "ep04")) == 1


def test_a_redo_names_its_step_and_notes_the_casebook(conn, book, capsys):
    argv = ["redo", CODEX, "episode", "ep04", "02", "--note", "wrong street",
            "--artefact", "episodes/ep04/plan.json", "--class", "plan_story"]
    assert studio_cli.main(argv, conn=conn) == 0
    (row,) = work_orders.pending_orders(conn, CODEX, "episode", "ep04")
    assert row["kind"] == "redo" and row["step_id"] == "02" and row["note"] == "wrong street"
    (note,) = casebook.read_rows(book / "casebook" / casebook.OWNER)
    assert note.fault_class == "plan_story" and note.path == "episodes/ep04/plan.json"


def test_a_redo_without_an_artefact_takes_the_steps_declared_output(conn, book):
    studio_cli.main(["redo", CODEX, "episode", "ep04", "02", "--note", "wrong street"], conn=conn)
    (note,) = casebook.read_rows(book / "casebook" / casebook.OWNER)
    assert note.path == "episodes/ep04/plan.json" and note.fault_class == "unknown"


def test_a_redo_whose_output_is_not_a_casebook_kind_asks_for_the_artefact(conn, book):
    with pytest.raises(SystemExit, match="--artefact"):
        studio_cli.main(["redo", CODEX, "episode", "ep04", "05", "--note", "off by a beat"], conn=conn)
    assert work_orders.pending_orders(conn, CODEX, "episode", "ep04") == []


def test_queue_is_not_a_subcommand_here(conn):
    with pytest.raises(SystemExit):
        studio_cli.main(["queue"], conn=conn)
