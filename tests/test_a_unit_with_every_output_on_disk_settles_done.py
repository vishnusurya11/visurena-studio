"""C2's map leaves a `skipped` event's row where it was, so a unit whose every
step was skipped (its outputs were already on disk) stays `blocked` until the
tick settles it (the note under C7 in the tracker): a blocked or queued row
whose every declared output of every step matches a file, and whose
deliverable exists, is `done` with the deliverable set and its `source` kept.
One missing output, or a row in any other state, and nothing moves.  The tick
also projects the unit's costs: GPU seconds off its clock, dollars off usage."""
from __future__ import annotations

import pytest

from studio import db, episode_home, registry, spend, tick

CODEX = "20260901000001"
REFS_OUT = ("refs/refs.json", "refs/characters/a/sheet.png", "refs/props/b/sheet.png",
            "refs/pack.jsonl", "cast/a/voice/design.wav", "refs/verdict.json", "refs/manifest.json")


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


def _write(book, rels):
    for rel in rels:
        (book / rel).parent.mkdir(parents=True, exist_ok=True)
        (book / rel).write_text("x", encoding="utf-8")


def _row(conn, stage="refs", unit="main"):
    return db.work_order(conn, CODEX, stage, unit)


def test_outputs_on_disk_needs_every_declared_output_of_every_step(book):
    assert not tick.outputs_on_disk(book, "refs", "main")
    _write(book, REFS_OUT[:-1])
    assert not tick.outputs_on_disk(book, "refs", "main")
    _write(book, REFS_OUT)
    assert tick.outputs_on_disk(book, "refs", "main")


def test_a_blocked_unit_with_every_output_on_disk_settles_done(conn, book):
    tick.materialize(conn, CODEX, "refs", ["main"])
    _write(book, REFS_OUT)
    assert tick.settle_skipped(conn, CODEX, "refs", "main", book)
    row = _row(conn)
    assert (row["state"], row["deliverable"], row["source"]) == ("done", "refs/verdict.json", "queue")
    assert row["step_id"] == registry.steps("refs")[-1]["id"] and row["finished_at"] and row["blocked_on"] is None


def test_one_missing_output_and_nothing_moves(conn, book):
    tick.materialize(conn, CODEX, "refs", ["main"])
    _write(book, REFS_OUT[1:])
    assert not tick.settle_skipped(conn, CODEX, "refs", "main", book)
    assert _row(conn)["state"] == "blocked" and _row(conn)["deliverable"] is None


@pytest.mark.parametrize("state", ["running", "failed", "deferred", "escalated", "held", "stale", "done"])
def test_a_row_in_any_other_state_is_not_settled(conn, book, state):
    db.upsert_work_order(conn, CODEX, "refs", "main", state=state)
    _write(book, REFS_OUT)
    assert not tick.settle_skipped(conn, CODEX, "refs", "main", book)
    assert _row(conn)["state"] == state
    assert not tick.settle_skipped(conn, CODEX, "refs", "other", book)


def test_a_stage_that_declares_no_deliverable_never_settles_from_disk(conn, book):
    tick.materialize(conn, CODEX, "analysis", ["book"])
    assert registry.deliverable_of("analysis") is None
    assert not tick.settle_skipped(conn, CODEX, "analysis", "book", book)
    assert _row(conn, "analysis", "book")["state"] == "blocked"


def test_a_unit_whose_every_step_was_skipped_is_done_after_the_tick(conn, book):
    _write(book, REFS_OUT)
    for entry in registry.steps("refs"):
        db.add_event(conn, CODEX, "refs", entry["id"], "skipped", run_id="r1", unit="main", detail="output exists")
    assert _row(conn)["state"] == "blocked"                    # C2's map: skipped moves nothing
    counts = tick.tick_stage(conn, CODEX, "refs", book)
    assert counts["settled"] == 1 and _row(conn)["state"] == "done" and _row(conn)["source"] == "run"
    assert tick.tick_stage(conn, CODEX, "refs", book)["settled"] == 0


def test_the_tick_projects_gpu_seconds_and_dollars_onto_the_row(conn, book):
    tick.materialize(conn, CODEX, "episode", ["ep04"])
    clock = book / "episodes" / "ep04" / "timing.jsonl"
    clock.parent.mkdir(parents=True)
    clock.write_text('{"stage": "takes", "seconds": 90.5}\n{"stage": "timeline", "seconds": 3}\n', encoding="utf-8")
    spend.record(conn, CODEX, "episode", "02", "workhorse", "priced-model", 100, 10, unit="ep04")
    conn.execute("UPDATE usage SET cost_usd = 0.25")
    fields = tick.project_costs(conn, CODEX, "episode", "ep04", book)
    assert fields == {"gpu_seconds": 90.5, "cost_usd": 0.25}
    row = _row(conn, "episode", "ep04")
    assert (row["gpu_seconds"], row["cost_usd"]) == (90.5, 0.25)
    assert tick.project_costs(conn, CODEX, "episode", "ep09", book) == {}
    tick.tick_stage(conn, CODEX, "episode", book)
    assert conn.execute("SELECT order_id FROM usage").fetchone()[0] == row["id"]
