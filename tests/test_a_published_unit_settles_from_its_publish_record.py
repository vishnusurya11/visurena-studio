"""A unit published outside the runner is done (owner report 2026-10-11: every
War of the Worlds and Scarlet episode is on the channel, yet the board showed
WotW ep01/02/05 queued, ep18 stale and Scarlet ep01/02/10-14 blocked on refs/04).
The disk's publish record -- youtube.json plus an upload row with a video id,
read by backfill.publish_row, the one parser -- settles a queued or blocked
row, or a running row whose lease ran out, as `done`: blocked_on cleared, the
deliverable the uploaded file's book-relative path (found by the upload's
sha8), a note naming the record.  A live run, a failed row, a row with no
upload and a done row are not touched.  Any row written as done loses its
blocked_on, and the tick clears one a done row still carries."""
from __future__ import annotations

import json

import pytest

from studio import db, episode_home, tick
from studio.youtube_publish import sha8

CODEX = "20260901000001"
PAST, FUTURE = "2026-01-01T00:00:00Z", "2999-01-01T00:00:00Z"


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


def _publish(book, unit="ep01", master="cut/master_iter3.mp4", upload=True):
    """The unit's master on disk, its youtube.json, and (when asked) its upload row."""
    home = book / "episodes" / unit
    (home / "cut").mkdir(parents=True, exist_ok=True)
    (home / "cut" / "master_iter1.mp4").write_bytes(b"an earlier cut")
    (home / master).write_bytes(f"the uploaded cut of {unit}".encode())
    (home / "youtube.json").write_text(json.dumps({"privacy": "public"}), encoding="utf-8")
    if upload:
        row = {"episode": int(unit[2:]), "video_id": f"vid{unit}", "sha8": sha8(home / master),
               "privacy": "public", "at": "2026-10-01T00:00:00"}
        with open(book / "uploads.jsonl", "a", encoding="utf-8") as fh:
            fh.write(json.dumps(row) + "\n")


def _row(conn, unit="ep01"):
    return db.work_order(conn, CODEX, "episode", unit)


def test_the_uploaded_file_is_found_by_the_uploads_sha8(book):
    _publish(book)
    digest = sha8(book / "episodes" / "ep01" / "cut" / "master_iter3.mp4")
    assert tick.uploaded_file(book, "ep01", digest) == "episodes/ep01/cut/master_iter3.mp4"
    assert tick.uploaded_file(book, "ep01", "deadbeef") is None
    assert tick.uploaded_file(book, "ep09", digest) is None


@pytest.mark.parametrize("state", ["queued", "blocked"])
def test_a_queued_or_blocked_published_unit_settles_done(conn, book, state):
    db.upsert_work_order(conn, CODEX, "episode", "ep01", state=state, blocked_on="refs/04", source="queue")
    _publish(book)
    assert tick.settle_published(conn, CODEX, "episode", "ep01", book)
    row = _row(conn)
    assert (row["state"], row["blocked_on"], row["source"]) == ("done", None, "queue")
    assert row["deliverable"] == "episodes/ep01/cut/master_iter3.mp4" and row["finished_at"]
    assert "publish record" in row["note"] and "videp01" in row["note"]


def test_a_running_row_whose_lease_ran_out_settles_and_a_live_one_does_not(conn, book):
    _publish(book, "ep01")
    _publish(book, "ep02")
    db.upsert_work_order(conn, CODEX, "episode", "ep01", state="running", lease_until=PAST)
    db.upsert_work_order(conn, CODEX, "episode", "ep02", state="running", lease_until=FUTURE)
    assert tick.settle_published(conn, CODEX, "episode", "ep01", book)
    assert not tick.settle_published(conn, CODEX, "episode", "ep02", book)
    assert (_row(conn)["state"], _row(conn, "ep02")["state"]) == ("done", "running")


def test_a_stale_row_whose_lease_expired_settles(conn, book):
    _publish(book)
    db.upsert_work_order(conn, CODEX, "episode", "ep01", state="stale", blocked_on="lease expired")
    assert tick.settle_published(conn, CODEX, "episode", "ep01", book)
    assert _row(conn)["state"] == "done"


@pytest.mark.parametrize("state", ["failed", "deferred", "escalated", "held", "done"])
def test_a_row_in_any_other_state_is_not_touched(conn, book, state):
    _publish(book)
    db.upsert_work_order(conn, CODEX, "episode", "ep01", state=state, deliverable="keep")
    assert not tick.settle_published(conn, CODEX, "episode", "ep01", book)
    assert (_row(conn)["state"], _row(conn)["deliverable"]) == (state, "keep")


def test_youtube_json_without_an_upload_row_is_not_a_publication(conn, book):
    _publish(book, upload=False)
    db.upsert_work_order(conn, CODEX, "episode", "ep01", state="queued")
    assert not tick.settle_published(conn, CODEX, "episode", "ep01", book)
    assert not tick.settle_published(conn, CODEX, "episode", "ep07", book)        # no row at all
    assert _row(conn)["state"] == "queued"


def test_an_upload_whose_file_is_gone_settles_on_its_youtube_json(conn, book):
    _publish(book)
    (book / "episodes" / "ep01" / "cut" / "master_iter3.mp4").unlink()
    db.upsert_work_order(conn, CODEX, "episode", "ep01", state="blocked")
    assert tick.settle_published(conn, CODEX, "episode", "ep01", book)
    assert _row(conn)["deliverable"] == "episodes/ep01/youtube.json"


def test_a_book_level_stage_never_settles_from_a_publish_record(conn, book):
    _publish(book)
    db.upsert_work_order(conn, CODEX, "refs", "main", state="blocked")
    assert not tick.settle_published(conn, CODEX, "refs", "main", book)


def test_the_tick_settles_it_before_promote_or_the_sweep_can_move_it(conn, book):
    _publish(book)
    db.upsert_work_order(conn, CODEX, "episode", "ep01", state="running", lease_until=PAST)
    counts = tick.tick(conn, book.parent, [CODEX], hold_path=book / "no_hold")
    assert counts["settled"] >= 1 and counts["stale"] == 0 and _row(conn)["state"] == "done"


def test_a_runners_tick_book_settles_it_too(conn, book):
    _publish(book)
    tick.materialize(conn, CODEX, "episode", ["ep01"])
    tick.tick_book(conn, CODEX)
    assert _row(conn)["state"] == "done"


def test_a_row_written_done_loses_its_blocked_on(conn):
    db.upsert_work_order(conn, CODEX, "episode", "ep03", state="blocked", blocked_on="refs/04")
    db.upsert_work_order(conn, CODEX, "episode", "ep03", state="done", blocked_on="refs/04")
    assert _row(conn, "ep03")["blocked_on"] is None


def test_the_tick_clears_the_blocked_on_a_done_row_still_carries(conn, book):
    db.upsert_work_order(conn, CODEX, "episode", "ep03", state="done")
    conn.execute("UPDATE work_orders SET blocked_on = 'refs/04' WHERE unit = 'ep03'")
    assert tick.clear_done_wait(conn, CODEX, "episode", "ep03")
    assert _row(conn, "ep03")["blocked_on"] is None
    assert not tick.clear_done_wait(conn, CODEX, "episode", "ep03")


def test_done_fields_never_carry_a_wait():
    assert db.done_waits_on_nothing({"state": "done", "blocked_on": "x"}) == {"state": "done", "blocked_on": None}
    assert db.done_waits_on_nothing({"state": "blocked", "blocked_on": "x"})["blocked_on"] == "x"
    assert db.done_waits_on_nothing({"flags": 2}) == {"flags": 2}
