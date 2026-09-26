"""A judge's signature reaches the Command Center's rows (decision 2026-09-25,
C3): when the step answerable for a gate completes, its chip carries the file,
the signer, the word and the rung, and the order's `verdicts` JSON carries the
gate with the sha8 it binds to and its fault count.  The projection reads the
file manifest.VERDICTS names for that gate and step; nothing here runs a step
or a model, and no runner wrote a row."""
from __future__ import annotations

import json
import os

import pytest

from studio import db, episode_home, eye_verdict, manifest, plan_verdict, refs_verdict, registry, verdict_rows

CODEX = "20260901000001"


@pytest.fixture()
def book(tmp_path, monkeypatch):
    """A library with one book folder named by the codex id, the way book_dir finds it."""
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


def _complete(conn, stage, step, unit):
    db.add_event(conn, CODEX, stage, step, "started", run_id="r1", unit=unit)
    db.add_event(conn, CODEX, stage, step, "completed", run_id="r1", unit=unit)


def _chip(conn, stage, unit, step):
    order_id = db.work_order(conn, CODEX, stage, unit)["id"]
    return conn.execute("SELECT * FROM work_steps WHERE order_id = ? AND step_id = ?",
                        (order_id, step)).fetchone()


def _verdicts(conn, stage, unit) -> dict:
    return json.loads(db.work_order(conn, CODEX, stage, unit)["verdicts"] or "{}")


def _signed_plan(book, unit="ep04"):
    plan = episode_home.write_json(book / "episodes" / unit / "plan.json", {"number": 4})
    plan_verdict.sign(plan, "the plan holds", signed_by="judge:plan@1",
                      faults=[{"kind": "story", "where": "shot_03"}], flagged=True)
    return plan


def test_a_signed_plan_reaches_step_02s_chip_and_the_orders_verdicts(conn, book):
    plan = _signed_plan(book)
    _complete(conn, "episode", "02", "ep04")
    chip = _chip(conn, "episode", "ep04", "02")
    assert chip["verdict_by"] == "judge:plan@1" and chip["verdict_word"] == "APPROVE"
    assert chip["verdict_path"] == "episodes/ep04/plan.verdict.json" and chip["terminal"] == ""
    got = _verdicts(conn, "episode", "ep04")
    assert got["PLAN"] == {"word": "APPROVE", "by": "judge:plan@1", "terminal": "",
                           "sha8": plan_verdict.plan_sha8(plan), "faults": 1,
                           "path": "episodes/ep04/plan.verdict.json"}


def test_the_look_verdict_reaches_refs_step_04_and_the_deliverable(conn, book):
    refs_verdict.sign(book, "the look holds", signed_by="judge:look@1")
    _complete(conn, "refs", "04", "main")
    chip = _chip(conn, "refs", "main", "04")
    assert (chip["verdict_by"], chip["verdict_word"], chip["verdict_path"]) == (
        "judge:look@1", "APPROVE", "refs/verdict.json")
    row = db.work_order(conn, CODEX, "refs", "main")
    assert row["state"] == "done" and row["deliverable"] == "refs/verdict.json"
    assert _verdicts(conn, "refs", "main")["LOOK"]["sha8"] == refs_verdict.pack_sha8(book)


def test_an_eye_flag_reaches_its_chip_with_the_rung(conn, book):
    panel = book / "episodes" / "ep04" / "storyboard" / "shot_01.png"
    panel.parent.mkdir(parents=True)
    panel.write_bytes(b"panel")
    eye_verdict.sign(panel.parent, [panel], "flagged", "kept best", signed_by="judge:panel_eye@1",
                     faults=[{"kind": "clones", "where": "shot_01"}], terminal="keep_best")
    _complete(conn, "episode", "08", "ep04")
    chip = _chip(conn, "episode", "ep04", "08")
    assert chip["verdict_word"] == "flagged" and chip["terminal"] == "keep_best"
    assert chip["verdict_path"].startswith("episodes/ep04/storyboard/eye_")
    got = _verdicts(conn, "episode", "ep04")["EYE_PANELS"]
    assert got["faults"] == 1 and got["sha8"] == eye_verdict.fingerprint([panel])


def test_a_step_that_signs_nothing_keeps_the_verdicts_the_order_has(conn, book):
    _signed_plan(book)
    _complete(conn, "episode", "02", "ep04")
    _complete(conn, "episode", "03", "ep04")
    assert _chip(conn, "episode", "ep04", "03")["verdict_by"] is None
    assert list(_verdicts(conn, "episode", "ep04")) == ["PLAN"]


def test_the_last_step_sets_the_deliverable_once_it_exists(conn, book):
    _complete(conn, "episode", "12", "ep04")
    assert db.work_order(conn, CODEX, "episode", "ep04")["deliverable"] is None
    episode_home.write_json(book / "episodes" / "ep04" / "manifest.json", {})
    _complete(conn, "episode", "12", "ep04")
    assert db.work_order(conn, CODEX, "episode", "ep04")["deliverable"] == "episodes/ep04/manifest.json"


def test_every_gate_names_the_step_whose_registry_row_writes_its_file():
    for stage, rows in manifest.VERDICTS.items():
        for gate, step, pattern in rows:
            assert pattern in registry.outputs_of(stage, step), (stage, gate, step)
    assert manifest.gates_of("episode", "02") == [("PLAN", "episodes/{unit}/plan.verdict.json")]
    assert manifest.gates_of("episode", "03") == [] and manifest.gates_of("analysis", "01") == []


def test_the_newest_signature_is_the_one_the_step_just_wrote(book):
    folder = book / "episodes" / "ep04" / "storyboard"
    folder.mkdir(parents=True)
    for name, age in (("eye_aaaaaaaa.json", 100), ("eye_bbbbbbbb.json", 0)):
        target = folder / name
        target.write_text("{}", encoding="utf-8")
        os.utime(target, (target.stat().st_atime, target.stat().st_mtime - age))
    assert verdict_rows.latest(book, "episodes/{unit}/storyboard/eye_*.json", "ep04") == (
        "episodes/ep04/storyboard/eye_bbbbbbbb.json")
    assert verdict_rows.latest(book, "episodes/{unit}/plan.verdict.json", "ep04") is None


def test_the_row_read_off_a_file_is_the_manifests_reading_plus_sha8_and_faults(book):
    plan = _signed_plan(book)
    got = verdict_rows.read_row(book, "PLAN", "episodes/ep04/plan.verdict.json")
    assert got["by"] == "judge:plan@1" and got["sha8"] == plan_verdict.plan_sha8(plan) and got["faults"] == 1
    plan_verdict.sign(plan, "looked")                       # the owner's hand: no faults field
    got = verdict_rows.read_row(book, "PLAN", "episodes/ep04/plan.verdict.json")
    assert got["by"] == "owner" and got["faults"] == 0


def test_a_half_written_verdict_never_fails_the_event(conn, book):
    target = book / "episodes" / "ep04" / "plan.verdict.json"
    target.parent.mkdir(parents=True)
    target.write_text("{", encoding="utf-8")
    _complete(conn, "episode", "02", "ep04")
    assert _chip(conn, "episode", "ep04", "02")["verdict_by"] is None
    assert _verdicts(conn, "episode", "ep04") == {}


def test_the_verdicts_json_merges_this_steps_gates_over_the_kept_ones():
    class Row(dict):
        __getitem__ = dict.get
    kept = Row(verdicts=json.dumps({"PLAN": {"word": "APPROVE"}}))
    merged = json.loads(db._merged_verdicts(kept, {"EYE_PANELS": {"word": "pass"}}))
    assert list(merged) == ["EYE_PANELS", "PLAN"]
    assert json.loads(db._merged_verdicts(None, {})) == {}
