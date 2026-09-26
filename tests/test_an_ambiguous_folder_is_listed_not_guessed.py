"""C8: a row the files do not settle is LISTED for the owner and never written
without --force: a folder outside the unit grammar (ep01_short), a live run
(a `started` with no terminal event inside six hours), a hand-signed verdict,
a published unit with no qc file.  The listing names each reason and counts
them in its totals."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from studio import backfill, db, episode_home, plan_verdict

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


def _episode(book, unit, qc=True, published=True):
    home = book / "episodes" / unit
    episode_home.write_json(home / "plan.json", {"number": 1})
    (home / "cut").mkdir(parents=True)
    (home / "cut" / "master_r2v.mp4").write_bytes(b"m")
    if qc:
        episode_home.write_json(home / "qc_r2v.json", {"passed": True})
    if published:
        episode_home.write_json(home / "youtube.json", {})
    return home


def test_a_folder_outside_the_unit_grammar_is_listed_and_not_written(book, conn):
    _episode(book, "ep01_short")
    entries = backfill.plan(conn, episode_home.LIBRARY)
    assert [e["row"]["unit"] for e in entries] == ["ep01_short"]
    assert entries[0]["ambiguous"] == "outside the unit grammar"
    assert backfill.write(conn, entries) == 0 and db.work_order(conn, CODEX, "episode", "ep01_short") is None
    assert backfill.write(conn, entries, force=True) == 1
    assert db.work_order(conn, CODEX, "episode", "ep01_short")["source"] == "backfill"


def test_a_hand_signed_verdict_is_ambiguous(book):
    home = _episode(book, "ep12")
    plan_verdict.sign(home / "plan.json", "Re-signed by hand")
    row = backfill.derive_unit(book, CODEX, "episode", "ep12", {})
    assert backfill.ambiguous(book, CODEX, "episode", "ep12", row, {}) == "hand-signed verdict: PLAN by owner"
    plan_verdict.sign(home / "plan.json", "the judge", signed_by="judge:plan@1")
    row = backfill.derive_unit(book, CODEX, "episode", "ep12", {})
    assert backfill.ambiguous(book, CODEX, "episode", "ep12", row, {}) is None


def test_a_published_unit_with_no_qc_file_is_ambiguous(book):
    _episode(book, "ep02", qc=False)
    row = backfill.derive_unit(book, CODEX, "episode", "ep02", {})
    assert row["state"] == "blocked"
    assert backfill.ambiguous(book, CODEX, "episode", "ep02", row, {}) == "published but no qc file"


def test_a_published_unit_whose_qc_did_not_pass_is_ambiguous_not_blocked_in_silence(book):
    """WotW ep05 went out on the owner's waiver with qc `passed: false`."""
    home = _episode(book, "ep05")
    episode_home.write_json(home / "qc_r2v.json", {"passed": False})
    row = backfill.derive_unit(book, CODEX, "episode", "ep05", {})
    assert row["state"] == "blocked"
    assert backfill.ambiguous(book, CODEX, "episode", "ep05", row, {}) == "published but qc did not pass"
    assert backfill.published_unsettled(home.parent / "nowhere") is None
    (home / "qc_r2v.json").write_text("{", encoding="utf-8")
    assert backfill.published_unsettled(home) == "published but qc did not pass"


def test_a_started_with_no_terminal_event_inside_six_hours_is_a_live_run(book, conn):
    _episode(book, "ep12")
    db.add_event(conn, CODEX, "episode", "09", "started", run_id="r9", unit="ep12")
    now = datetime.now(timezone.utc)
    live = backfill.events_summary(conn, CODEX, "episode", "ep12", now=now)
    assert live["live"] is True
    row = backfill.derive_unit(book, CODEX, "episode", "ep12", live)
    assert backfill.ambiguous(book, CODEX, "episode", "ep12", row, live).startswith("a live run (r9 started ")
    stale = backfill.events_summary(conn, CODEX, "episode", "ep12", now=now + timedelta(hours=9))
    assert stale["live"] is False
    assert backfill.is_live(live["last"]["ts"], "completed", now) is False


def test_every_reason_is_named_together(book, conn):
    home = _episode(book, "ep01_short", qc=False)
    plan_verdict.sign(home / "plan.json", "by hand")
    row = backfill.derive_unit(book, CODEX, "episode", "ep01_short", {})
    got = backfill.ambiguous(book, CODEX, "episode", "ep01_short", row, {})
    assert got == "outside the unit grammar; hand-signed verdict: PLAN by owner; published but no qc file"


def test_the_listing_names_each_unit_its_reason_and_the_totals(book, conn):
    _episode(book, "ep01_short")
    _episode(book, "ep03")
    text = backfill.listing(backfill.plan(conn, episode_home.LIBRARY))
    lines = text.splitlines()
    assert lines[0].startswith("codex") and "ep01_short" in lines[1] and "ep03" in lines[2]
    assert "AMBIGUOUS: outside the unit grammar" in lines[1] and "done" in lines[2]
    assert "rows: 2  derivable: 1  ambiguous: 1  live-skipped: 0" in text
    assert f"by book: {CODEX} 2" in text and "by state: done 2" in text
    assert backfill.listing([]).splitlines()[-3] == "rows: 0  derivable: 0  ambiguous: 0  live-skipped: 0"


def test_the_line_shows_the_verdict_words_flags_gpu_hours_and_the_existing_row():
    row = {"codex_id": CODEX, "stage": "episode", "unit": "ep03", "state": "done", "step_id": "11",
        "verdicts": '{"PLAN": {"word": "APPROVE"}, "EYE_TAKES": {"word": "flagged"}}',
        "flags": 2, "gpu_seconds": 5400.0}
    line = backfill.line_of({"row": row, "ambiguous": None, "live_run": None, "existing_state": "running"})
    assert "EYE_TAKES=flagged PLAN=APPROVE" in line and "flags 2" in line and "gpu 1.5h" in line
    assert line.endswith("(row: running)")
    assert backfill.verdict_words({"verdicts": None}) == "-"
