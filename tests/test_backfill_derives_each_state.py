"""C8: every state the files can imply.  `deferred` from a plan.deferred.json
without a signed plan; `blocked` at the last step with an output when the unit
stopped mid-way; `done` grandfathered when no verdict file exists; and the
publish row from youtube.json + uploads.jsonl, valid in work_orders although
the registry has no `publish` stage (so no view)."""
from __future__ import annotations

import json
import sqlite3

import pytest

from studio import backfill, db, episode_home, plan_verdict

CODEX = "20260901000001"


@pytest.fixture()
def book(tmp_path, monkeypatch):
    library = tmp_path / "library"
    folder = library / f"{CODEX}_a-book"
    folder.mkdir(parents=True)
    monkeypatch.setattr(episode_home, "LIBRARY", library)
    return folder


@pytest.fixture()
def conn(tmp_path):
    connection = db.get_connection(tmp_path / "t.db")
    db.init_db(connection)
    db.insert_codex(connection, "Book", codex_id=CODEX)
    return connection


def _uploads(book, rows):
    with (book / "uploads.jsonl").open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")


def test_a_deferred_plan_is_deferred_at_the_plan_step(book):
    home = book / "episodes" / "ep13"
    episode_home.write_json(home / "plan.json", {"number": 13})
    episode_home.write_json(home / "plan.deferred.json", {"verdict": "DEFERRED", "passes": 5})
    row = backfill.derive_unit(book, CODEX, "episode", "ep13", {})
    assert row["state"] == "deferred" and row["step_id"] == "02" and row["deliverable"] is None
    assert row["progress"] == "0/12" and row["finished_at"] is None


def test_a_signed_plan_beside_an_old_deferral_is_not_deferred(book):
    home = book / "episodes" / "ep13"
    plan = episode_home.write_json(home / "plan.json", {"number": 13})
    episode_home.write_json(home / "plan.deferred.json", {"verdict": "DEFERRED"})
    plan_verdict.sign(plan, "holds", signed_by="judge:plan@1")
    assert backfill.derive_unit(book, CODEX, "episode", "ep13", {})["state"] == "blocked"


def test_a_unit_that_stopped_mid_way_is_blocked_at_its_last_step_with_an_output(book):
    home = book / "episodes" / "ep05"
    episode_home.write_json(home / "plan.json", {"number": 5})
    episode_home.write_json(home / "placed.json", {})
    (home / "audio" / "lines").mkdir(parents=True)
    (home / "audio" / "lines" / "l01.wav").write_bytes(b"wav")
    row = backfill.derive_unit(book, CODEX, "episode", "ep05", {})
    assert (row["state"], row["step_id"], row["progress"]) == ("blocked", "05", "1/12")
    assert row["note"] == "ts:mtime"


def test_state_of_reads_done_deferred_then_blocked(book):
    home = book / "episodes" / "ep02"
    assert backfill.state_of(book, "episodes/ep02", "episodes/ep02/manifest.json", "02") == ("done", "02")
    assert backfill.state_of(book, "episodes/ep02", None, "02") == ("blocked", "02")
    episode_home.write_json(home / "plan.deferred.json", {})
    assert backfill.state_of(book, "episodes/ep02", None, "02") == ("deferred", "02")
    assert backfill.state_of(book, "episodes/ep02", None, None) == ("deferred", None)


def test_a_book_level_output_another_episode_made_does_not_move_this_units_step(book):
    """Step 03's places and step 01's refs.json are book-level: ep13 with only a
    plan is at step 02 although refs/locations/ is full of ep12's pictures."""
    (book / "refs" / "locations" / "common").mkdir(parents=True)
    (book / "refs" / "locations" / "common" / "wide.png").write_bytes(b"png")
    episode_home.write_json(book / "episodes" / "ep13" / "plan.json", {"number": 13})
    outputs = backfill.step_outputs(book, "episode", "ep13")
    assert outputs["03"] == (True, ["refs/locations/common/wide.png"])
    assert backfill.last_step("episode", outputs) == "02"
    assert backfill.last_step("refs", {"01": (True, ["refs/refs.json"]), "02": (False, [])}) == "01"
    assert backfill.last_step("episode", {}) is None


def test_the_note_names_grandfathering_and_mtime_clocks():
    assert backfill.note_of({}, True, True) == "grandfathered: no verdict file; ts:mtime"
    assert backfill.note_of({"PLAN": {}}, True, False) is None
    assert backfill.note_of({}, False, True) == "ts:mtime"


def test_the_publish_row_comes_from_youtube_json_and_the_upload_ledger(book):
    home = book / "episodes" / "ep01"
    episode_home.write_json(home / "youtube.json", {"privacy": "private"})
    _uploads(book, [{"episode": 1, "video_id": "VwS0kox9DSA", "sha8": "2ca8a6fa", "privacy": "private",
                     "at": "2026-09-19T03:43:45"},
                    {"episode": 1, "video_id": "VwS0kox9DSA", "privacy": "public", "at": "2026-09-19"},
                    {"episode": 2, "video_id": "HBDGuVyXCR4", "sha8": "ac23326a", "privacy": "private"}])
    row = backfill.publish_row(book, CODEX, "ep01")
    assert (row["stage"], row["unit"], row["kind"], row["home"]) == (
        "publish", "2ca8a6fa@youtube", "master", "publish/2ca8a6fa@youtube")
    assert row["state"] == "done" and row["deliverable"] == "episodes/ep01/youtube.json"
    assert row["note"] == "video VwS0kox9DSA public; from ep01" and row["number"] == 1
    assert row["finished_at"] == "2026-09-19T03:43:45" and row["source"] == "backfill"


def test_no_upload_or_no_youtube_json_is_no_publish_row(book):
    home = book / "episodes" / "ep03"
    episode_home.write_json(home / "youtube.json", {})
    assert backfill.publish_row(book, CODEX, "ep03") is None
    _uploads(book, [{"episode": 3, "video_id": "x", "sha8": "f8bf7814"}])
    assert backfill.publish_row(book, CODEX, "ep03") is not None
    assert backfill.publish_row(book, CODEX, "ep04") is None
    assert backfill.upload_rows(book, 3)[0]["sha8"] == "f8bf7814" and backfill.upload_rows(book, 9) == []


def test_a_publish_row_is_valid_in_work_orders_though_no_view_exists(book, conn):
    episode_home.write_json(book / "episodes" / "ep01" / "youtube.json", {})
    _uploads(book, [{"episode": 1, "video_id": "v", "sha8": "2ca8a6fa", "privacy": "public"}])
    entry = backfill.publish_entry(conn, backfill.publish_row(book, CODEX, "ep01"))
    assert entry["caveat"] and entry["ambiguous"] is None and entry["live_run"] is None
    assert backfill.write(conn, [entry]) == 1
    row = db.work_order(conn, CODEX, "publish", "2ca8a6fa@youtube")
    assert row["state"] == "done" and row["home"] == "publish/2ca8a6fa@youtube" and row["source"] == "backfill"
    with pytest.raises(sqlite3.OperationalError):
        conn.execute("SELECT * FROM publish_orders")
    assert list(conn.execute("SELECT * FROM episode_orders")) == []
