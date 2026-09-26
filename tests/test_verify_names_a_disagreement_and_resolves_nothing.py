"""`studio.py verify` (decision 2026-09-25, "events vs rows"): rows are diffed
against the disk and a disagreement is named and marked `stale`; nothing is
resolved.  A done row whose deliverable is gone is stale under 'deliverable
missing'; a done row whose signature no longer names the artefact is stale
under the gate (db.mark_stale_verdicts); a stale row does not go back to done
when the file returns -- only a run or an order moves it."""
from __future__ import annotations

import pytest

from studio import db, episode_home, plan_verdict, registry, tick

CODEX = "20260901000001"


@pytest.fixture()
def book(tmp_path, monkeypatch):
    root = tmp_path / "library"
    folder = root / f"{CODEX}_a-book"
    folder.mkdir(parents=True)
    monkeypatch.setattr(episode_home, "LIBRARY", root)
    return folder


@pytest.fixture()
def conn(tmp_path):
    connection = db.get_connection(tmp_path / "t.db")
    db.init_db(connection)
    db.insert_codex(connection, "Book", codex_id=CODEX)
    return connection


def _delivered(conn, book):
    """A unit run to done by its events, with a signed plan and its manifest on disk."""
    plan = episode_home.write_json(book / "episodes" / "ep04" / "plan.json", {"number": 4})
    plan_verdict.sign(plan, "holds", signed_by="judge:plan@1")
    episode_home.write_json(book / "episodes" / "ep04" / "manifest.json", {})
    for entry in registry.steps("episode"):
        db.add_event(conn, CODEX, "episode", entry["id"], "started", run_id="r1", unit="ep04")
        db.add_event(conn, CODEX, "episode", entry["id"], "completed", run_id="r1", unit="ep04")
    return plan


def _row(conn):
    return db.work_order(conn, CODEX, "episode", "ep04")


def test_a_unit_whose_rows_and_disk_agree_has_nothing_to_say(conn, book):
    _delivered(conn, book)
    assert _row(conn)["deliverable"] == "episodes/ep04/manifest.json"
    assert tick.verify(conn, CODEX, "episode", "ep04", book) == []
    assert _row(conn)["state"] == "done"


def test_a_done_row_whose_deliverable_is_gone_is_stale_and_named(conn, book):
    _delivered(conn, book)
    (book / "episodes" / "ep04" / "manifest.json").unlink()
    assert tick.verify(conn, CODEX, "episode", "ep04", book) == [
        "episode/ep04: deliverable missing: episodes/ep04/manifest.json"]
    assert (_row(conn)["state"], _row(conn)["blocked_on"]) == ("stale", "deliverable missing")


def test_a_moved_signature_is_named_by_its_gate(conn, book):
    plan = _delivered(conn, book)
    episode_home.write_json(plan, {"number": 4, "title": "rewritten after the signature"})
    assert tick.verify(conn, CODEX, "episode", "ep04", book) == ["episode/ep04: PLAN signed another sha8"]
    assert (_row(conn)["state"], _row(conn)["blocked_on"]) == ("stale", "PLAN")


def test_verify_resolves_nothing_when_the_file_comes_back(conn, book):
    _delivered(conn, book)
    (book / "episodes" / "ep04" / "manifest.json").unlink()
    tick.verify(conn, CODEX, "episode", "ep04", book)
    episode_home.write_json(book / "episodes" / "ep04" / "manifest.json", {})
    assert tick.verify(conn, CODEX, "episode", "ep04", book) == []
    assert _row(conn)["state"] == "stale"


def test_a_unit_with_no_row_is_a_disagreement_too(conn, book):
    assert tick.verify(conn, CODEX, "episode", "ep09", book) == ["episode/ep09: no row"]


def test_a_row_not_done_is_not_read_against_the_disk(conn, book):
    db.upsert_work_order(conn, CODEX, "episode", "ep04", state="queued", deliverable="episodes/ep04/manifest.json")
    assert tick.verify(conn, CODEX, "episode", "ep04", book) == []
    assert _row(conn)["state"] == "queued"
