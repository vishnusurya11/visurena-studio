"""A signature names the bytes it was given (plan_verdict, refs_verdict,
eye_verdict all say so).  The Command Center keeps that rule on its rows
(decision 2026-09-25, the state machine): a done unit whose recorded sha8 no
longer matches the artefact as it stands is `stale`.  `db.mark_stale_verdicts`
is verify's call (C7), never add_event's; the hashing is the signers' own."""
from __future__ import annotations

import pytest

from studio import db, episode_home, eye_verdict, manifest, plan_verdict, refs_verdict, registry, verdict_rows

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


def _signed_unit(book):
    """A plan and one panel, both signed."""
    plan = episode_home.write_json(book / "episodes" / "ep04" / "plan.json", {"number": 4})
    plan_verdict.sign(plan, "holds", signed_by="judge:plan@1")
    panel = book / "episodes" / "ep04" / "storyboard" / "shot_01.png"
    panel.parent.mkdir(parents=True)
    panel.write_bytes(b"panel")
    eye_verdict.sign(panel.parent, [panel], "pass", "clean", signed_by="judge:panel_eye@1")
    return plan, panel


def _run_to_done(conn):
    for entry in registry.steps("episode"):
        db.add_event(conn, CODEX, "episode", entry["id"], "started", run_id="r1", unit="ep04")
        db.add_event(conn, CODEX, "episode", entry["id"], "completed", run_id="r1", unit="ep04")


def _state(conn):
    return db.work_order(conn, CODEX, "episode", "ep04")["state"]


def test_an_edited_plan_flips_the_done_row_to_stale(conn, book):
    plan, _ = _signed_unit(book)
    _run_to_done(conn)
    assert _state(conn) == "done"
    episode_home.write_json(plan, {"number": 4, "title": "rewritten after the signature"})
    assert db.mark_stale_verdicts(conn, CODEX, "episode", "ep04", book) == ["PLAN"]
    row = db.work_order(conn, CODEX, "episode", "ep04")
    assert row["state"] == "stale" and row["blocked_on"] == "PLAN"


def test_an_untouched_unit_stays_done(conn, book):
    _signed_unit(book)
    _run_to_done(conn)
    assert db.mark_stale_verdicts(conn, CODEX, "episode", "ep04", book) == []
    assert _state(conn) == "done"


def test_a_redrawn_panel_is_stale_under_its_eye(conn, book):
    _, panel = _signed_unit(book)
    _run_to_done(conn)
    panel.write_bytes(b"redrawn")
    assert db.mark_stale_verdicts(conn, CODEX, "episode", "ep04", book) == ["EYE_PANELS"]
    assert _state(conn) == "stale"


def test_a_row_that_is_not_done_is_left_as_it_is(conn, book):
    plan, _ = _signed_unit(book)
    db.add_event(conn, CODEX, "episode", "02", "started", run_id="r1", unit="ep04")
    db.add_event(conn, CODEX, "episode", "02", "completed", run_id="r1", unit="ep04")
    episode_home.write_json(plan, {"number": 5})
    assert db.mark_stale_verdicts(conn, CODEX, "episode", "ep04", book) == []
    assert _state(conn) == "running"
    assert db.mark_stale_verdicts(conn, CODEX, "episode", "ep09", book) == []   # no row at all


def test_the_artefacts_sha8_is_the_signers_own_word(book):
    plan, panel = _signed_unit(book)
    assert verdict_rows.artefact_sha8(book, "PLAN", "ep04") == plan_verdict.plan_sha8(plan)
    assert verdict_rows.artefact_sha8(book, "EYE_PANELS", "ep04") == eye_verdict.fingerprint([panel])
    pack = book / "refs" / "pack.jsonl"
    pack.parent.mkdir()
    pack.write_text('{"path": "x"}\n', encoding="utf-8")
    assert verdict_rows.artefact_sha8(book, "LOOK", "main") == refs_verdict.pack_sha8(book)
    master = episode_home.master_path(book, 4, "r2v")
    master.parent.mkdir(parents=True)
    master.write_bytes(b"the cut")
    assert verdict_rows.artefact_sha8(book, "MASTER", "ep04") == manifest.sha8_of(master)
    assert verdict_rows.artefact_sha8(book, "EYE_TAKES", "ep04") == ""     # nothing to sign yet


def test_stale_gates_compares_the_record_with_the_disk_and_skips_a_record_without_a_sha8(book):
    plan, panel = _signed_unit(book)
    recorded = {"PLAN": {"sha8": plan_verdict.plan_sha8(plan)},
                "EYE_PANELS": {"sha8": "00000000"},
                "MASTER": {"sha8": ""}}
    assert verdict_rows.stale_gates(book, "ep04", recorded) == ["EYE_PANELS"]


def test_what_each_gate_signs_is_a_path_the_registry_declares():
    declared = {p for stage in ("episode", "refs") for s in registry.steps(stage)
                for p in registry.inputs_of(stage, s["id"]) + registry.outputs_of(stage, s["id"])}
    assert set(verdict_rows.SIGNS) == {g for rows in manifest.VERDICTS.values() for g, _, _ in rows}
    assert all(pattern in declared for pattern in verdict_rows.SIGNS.values())
