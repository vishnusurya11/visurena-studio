"""C8 (decision 2026-09-25, "Migration, zero loss"): the work-order row a unit's
FILES imply.  A published episode from before the judges -- a plan, a master
under cut/, a qc_r2v.json that passed, a youtube.json, no verdict file -- is
`done` and grandfathered; a manifest is the deliverable before the legacy
pair; a judge's signature reaches the verdicts JSON; the clock gives the GPU
seconds and the events the attempts.  Tmp library, tmp DB, nothing paid."""
from __future__ import annotations

import json
import os

import pytest

from studio import audit_rows, backfill, db, episode_home, plan_verdict, refs_verdict

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


def published(book, unit="ep11", passed=True, qc=True):
    """The legacy published shape: plan, placed, master, qc, youtube.json."""
    home = book / "episodes" / unit
    episode_home.write_json(home / "plan.json", {"number": 11})
    episode_home.write_json(home / "placed.json", {})
    (home / "cut").mkdir(parents=True)
    (home / "cut" / "master_r2v.mp4").write_bytes(b"master")
    if qc:
        episode_home.write_json(home / "qc_r2v.json", {"passed": passed, "sha8": "d8833608"})
    episode_home.write_json(home / "youtube.json", {"title": "Ep 11", "privacy": "private"})
    return home


def test_a_published_episode_with_no_verdict_file_is_done_and_grandfathered(book):
    published(book)
    row = backfill.derive_unit(book, CODEX, "episode", "ep11", {})
    assert (row["state"], row["step_id"], row["number"]) == ("done", "11", 11)
    assert row["deliverable"] == "episodes/ep11/cut/master_r2v.mp4"
    assert row["source"] == "backfill" and json.loads(row["verdicts"]) == {}
    assert "grandfathered: no verdict file" in row["note"] and "ts:mtime" in row["note"]
    assert row["started_at"] and row["finished_at"] and row["attempts"] == 0


def test_a_qc_that_did_not_pass_leaves_the_unit_blocked_at_its_last_step(book):
    published(book, passed=False)
    row = backfill.derive_unit(book, CODEX, "episode", "ep11", {})
    assert row["state"] == "blocked" and row["step_id"] == "11" and row["deliverable"] is None
    assert row["finished_at"] is None and "grandfathered" not in (row["note"] or "")


def test_the_manifest_is_the_deliverable_before_the_legacy_pair(book):
    home = published(book, "ep12")
    episode_home.write_json(home / "manifest.json", {})
    row = backfill.derive_unit(book, CODEX, "episode", "ep12", {})
    assert row["deliverable"] == "episodes/ep12/manifest.json" and row["step_id"] == "12"
    assert backfill.legacy_deliverable(book, "episodes/ep12") == "episodes/ep12/cut/master_r2v.mp4"


def test_a_signed_plan_reaches_the_verdicts_and_the_audit_rows_the_flags(book):
    home = published(book)
    plan_verdict.sign(home / "plan.json", "holds", signed_by="judge:plan@1")
    audit_rows.append(book, {"unit": "ep11", "gate": "EYE_TAKES", "judge": "judge:take_eye@1",
                             "terminal": "keep_best"})
    row = backfill.derive_unit(book, CODEX, "episode", "ep11", {})
    assert json.loads(row["verdicts"])["PLAN"]["by"] == "judge:plan@1"
    assert row["flags"] == 1 and "grandfathered" not in (row["note"] or "")


def test_gpu_seconds_come_from_the_clock_and_attempts_and_clocks_from_the_events(book, conn):
    home = published(book)
    with (home / "timing.jsonl").open("w", encoding="utf-8") as fh:
        fh.write(json.dumps({"stage": "takes", "seconds": 100.0}) + "\n")
        fh.write(json.dumps({"stage": "respot", "seconds": 5.0}) + "\n")
    for run in ("r1", "r2"):
        db.add_event(conn, CODEX, "episode", "09", "started", run_id=run, unit="ep11")
        db.add_event(conn, CODEX, "episode", "09", "completed", run_id=run, unit="ep11")
    events = backfill.events_summary(conn, CODEX, "episode", "ep11")
    row = backfill.derive_unit(book, CODEX, "episode", "ep11", events)
    assert row["gpu_seconds"] == pytest.approx(100.0) and row["attempts"] == 2
    assert row["started_at"] == events["started_at"] and "ts:mtime" not in (row["note"] or "")


def test_events_summary_reads_passes_the_clocks_and_the_last_event(conn):
    assert backfill.events_summary(conn, CODEX, "episode", "ep11") == {}
    db.add_event(conn, CODEX, "refs", "04", "started", run_id="r1", unit="main")
    db.add_event(conn, CODEX, "refs", "04", "failed", run_id="r1", unit="main")
    db.add_event(conn, CODEX, "refs", "04", "started", run_id="r2", unit="main")
    db.add_event(conn, CODEX, "refs", "04", "completed", run_id="r2", unit="main")
    got = backfill.events_summary(conn, CODEX, "refs", "main")
    assert got["attempts"] == 2 and got["status"] == {"04": "completed"} and not got["live"]
    assert got["finished_at"] == got["last"]["ts"] and got["last"]["run_id"] == "r2"


def test_a_refs_unit_derives_from_its_verdict_file(book):
    (book / "refs").mkdir()
    (book / "refs" / "refs.json").write_text("{}", encoding="utf-8")
    assert backfill.derive_unit(book, CODEX, "refs", "main", {})["state"] == "blocked"
    refs_verdict.sign(book, "the look holds", signed_by="judge:look@1")
    row = backfill.derive_unit(book, CODEX, "refs", "main", {})
    assert row["state"] == "done" and row["deliverable"] == "refs/verdict.json"
    assert json.loads(row["verdicts"])["LOOK"]["by"] == "judge:look@1" and row["number"] is None


def test_a_stage_that_declares_no_outputs_derives_nothing(book):
    assert backfill.derive_unit(book, CODEX, "analysis", "book", {}) is None
    assert backfill.units_of(book, "analysis") == [] and backfill.units_of(book, "episode") == []
    published(book)
    (book / "refs").mkdir()
    assert backfill.units_of(book, "episode") == ["ep11"] and backfill.units_of(book, "refs") == ["main"]


def test_step_outputs_say_which_steps_have_every_declared_file(book):
    published(book)
    outputs = backfill.step_outputs(book, "episode", "ep11")
    assert outputs["05"] == (True, ["episodes/ep11/placed.json"])
    assert outputs["02"][0] is False and outputs["02"][1] == ["episodes/ep11/plan.json"]
    assert outputs["09"] == (False, [])


def test_mtimes_are_the_earliest_and_latest_file_in_utc(book):
    home = published(book)
    old = home / "plan.json"
    os.utime(old, (old.stat().st_atime, old.stat().st_mtime - 3600))
    first, last = backfill.mtimes(book, ["episodes/ep11/plan.json", "episodes/ep11/placed.json", "missing"])
    assert first < last and first.endswith("Z") and backfill.mtimes(book, []) == (None, None)
    assert backfill.number_of("ep11") == 11 and backfill.number_of("main") is None
