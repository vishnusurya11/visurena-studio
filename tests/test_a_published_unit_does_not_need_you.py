"""The board honours the owner's 2026-10-01 ruling ("no human input at
publish": judge-signed terminals auto-clear the publish lock).  A done unit
that is on the channel does not need the owner: it shows `done`, keeps its
gate chips as the audit trail, and is in neither Needs you nor the inbox
count.  A done unit with flags that is NOT published still shows `flagged`
and needs him until he acknowledges it -- and the department page and the
inbox read that through one function, views.flags_open.  Published means the
publish record (youtube.json plus an upload row with a video id), never a
youtube.json alone: the writer drafts that file before the upload."""
from __future__ import annotations

import json

import pytest

from command_center_fixtures import CODEX, make_library, seed
from studio import db, work_orders
from studio.command_center import views

VERDICTS = {"PLAN": {"word": "APPROVE", "faults": 0}, "MASTER": {"word": "", "faults": 2}}


@pytest.fixture()
def library(tmp_path, monkeypatch):
    return make_library(tmp_path, monkeypatch)


@pytest.fixture()
def conn(tmp_path, library):
    connection = db.get_connection(tmp_path / "t.db")
    db.init_db(connection)
    db.insert_codex(connection, "A Book", codex_id=CODEX)
    seed(connection, library)
    db.upsert_work_order(connection, CODEX, "episode", "ep03", verdicts=json.dumps(VERDICTS))
    return connection


def _upload(library, number=3):
    book = library / f"{CODEX}_a-book"
    row = {"episode": number, "video_id": "abc123", "sha8": "0badf00d", "privacy": "public"}
    with open(book / "uploads.jsonl", "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row) + "\n")


def _ep03(rows):
    return next(r for r in rows if r["unit"] == "ep03")


def test_a_youtube_json_alone_is_not_published(conn, library):
    row = db.work_order(conn, CODEX, "episode", "ep03")
    assert views.published(conn, dict(row)) is False
    _upload(library)
    assert views.published(conn, dict(row)) is True


def test_an_unpublished_flagged_unit_is_open_until_acknowledged(conn):
    row = dict(db.work_order(conn, CODEX, "episode", "ep03"))
    assert views.flags_open(conn, row) is True
    work_orders.order(conn, "acknowledge", "unit", codex_id=CODEX, stage="episode", unit="ep03",
                      note=db.ack_note(db.work_order(conn, CODEX, "episode", "ep03"), None))
    assert views.flags_open(conn, row) is False


def test_a_published_flagged_unit_is_not_open(conn, library):
    _upload(library)
    assert views.flags_open(conn, dict(db.work_order(conn, CODEX, "episode", "ep03"))) is False


def test_a_clean_or_unfinished_row_has_no_open_flags(conn):
    assert views.flags_open(conn, {"state": "done", "flags": 0, "codex_id": CODEX, "stage": "episode",
                                   "unit": "ep03"}) is False
    assert views.flags_open(conn, {"state": "running", "flags": 4, "codex_id": CODEX, "stage": "episode",
                                   "unit": "ep04"}) is False


def test_a_published_unit_leaves_needs_you_and_the_inbox(conn, library):
    assert "ep03" in [r["unit"] for r in views.attention(conn)]
    before = views.inbox_count(conn)
    _upload(library)
    assert "ep03" not in [r["unit"] for r in views.attention(conn)]
    assert views.inbox_count(conn) == before - 1


def test_the_department_shows_a_published_unit_done_with_its_chips(conn, library):
    assert _ep03(views.department(conn, "episode")["rows"])["shown"] == "flagged"
    _upload(library)
    dept = views.department(conn, "episode")
    ep03 = _ep03(dept["rows"])
    assert (ep03["shown"], ep03["glyph"], ep03["css"]) == ("done", "✓", "green")
    assert any(c["glyph"] == "⚑2" for c in ep03["strip"])                # the audit trail stays
    assert dept["counts"].get("flagged", 0) == 0


def test_the_department_and_the_inbox_agree_on_an_acknowledged_unit(conn):
    work_orders.order(conn, "acknowledge", "unit", codex_id=CODEX, stage="episode", unit="ep03",
                      note=db.ack_note(db.work_order(conn, CODEX, "episode", "ep03"), None))
    assert _ep03(views.department(conn, "episode")["rows"])["shown"] == "done"
    assert "ep03" not in [r["unit"] for r in views.attention(conn)]


def test_the_lane_and_the_book_read_the_same_rule(conn, library):
    _upload(library)
    assert views.lane(conn, "episode")["counts"].get("flagged", 0) == 0
    assert views.book(conn, library, CODEX)["cells"]["episode"]["ep03"]["state"] == "done"


def test_without_a_connection_a_row_view_keeps_the_raw_rule():
    row = views.row_view({"state": "done", "flags": 2, "stage": "episode", "unit": "ep03"})
    assert row["shown"] == "flagged"


def test_the_sidebar_dots_count_a_published_unit_done(conn, library):
    from studio.command_center import pulse
    assert pulse.dept_dots(conn)["episode"].get("flagged") == 1
    _upload(library)
    dots = pulse.dept_dots(conn)["episode"]
    assert dots.get("flagged", 0) == 0 and dots.get("done", 0) >= 1


def test_a_dot_moves_from_one_state_to_another():
    from studio.command_center import pulse
    counts = {"flagged": 1, "done": 2}
    pulse.move_dot(counts, "flagged", "done")
    assert counts == {"done": 3}
