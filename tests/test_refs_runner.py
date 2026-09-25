"""refs.py: the refs department's runner.  The registry's ids are the modules'
ids; every step is bracketed in events on unit "main"; a book is ready when
the stage it requires has completed; the LOOK step signs in the judge's name
(an empty pack reads nothing) and the run completes (exit 0)."""
from __future__ import annotations

import pytest

import refs
from studio import db, refs_run, registry, step_runner


@pytest.fixture()
def conn(tmp_path):
    connection = db.get_connection(tmp_path / "t.db")
    db.init_db(connection)
    return connection


@pytest.fixture()
def book(tmp_path, monkeypatch):
    book = tmp_path / "book"
    (book / "refs").mkdir(parents=True)
    monkeypatch.setattr(refs_run.episode_home, "book_dir", lambda codex_id: book)
    return book


def opts(tmp_path):
    return dict(logs_root=tmp_path / "logs", busy=lambda: False,
                hold=tmp_path / "HOLD", launch=lambda cmd: 0)


def test_the_registry_and_the_step_modules_agree_on_ids_and_names():
    steps = step_runner.load_steps("refs")
    assert [s.STEP_ID for s in steps] == ["01", "02", "03", "04"]
    assert [s.NAME for s in steps] == [e["name"] for e in registry.steps("refs")]
    assert [s.GPU for s in steps] == [False, True, True, True]


def test_ready_needs_the_required_analysis_step_and_not_a_finished_refs_stage(conn):
    codex = db.insert_codex(conn, "Book", codex_id="20260901000001")
    assert refs.ready(conn) == []
    db.add_event(conn, codex, "analysis", "05", "completed")
    assert refs.ready(conn) == [codex]
    db.add_event(conn, codex, "refs", "04", "completed", unit="main")
    assert refs.ready(conn) == []


def test_a_run_brackets_every_step_on_unit_main_and_the_judge_signs_the_look(conn, tmp_path, book, capsys):
    codex = db.insert_codex(conn, "Book", codex_id="20260901000001")
    outcome = refs.process(conn, codex, ["--chapter=1", "--cast=a=Alpha:male"], **opts(tmp_path))
    assert outcome == "completed"
    assert db.unit_status(conn, codex, "refs", "main") == {
        "01": "completed", "02": "skipped", "03": "completed", "04": "completed"}
    assert conn.execute("SELECT COUNT(*) FROM events WHERE unit IS NULL").fetchone()[0] == 0
    assert "OWNER" not in capsys.readouterr().out
    from studio import refs_verdict
    assert refs_verdict.current(book)["signed_by"] == "judge:look@1"
    assert db.get_codex(conn, codex)["refs_status"] == "completed"


def test_main_exits_0_when_the_judge_signs_and_again_when_the_book_is_done(conn, tmp_path, book):
    codex = db.insert_codex(conn, "Book", codex_id="20260901000001")
    assert refs.main([codex, "--chapter=1", "--cast=a"], conn=conn, **opts(tmp_path)) == 0
    from studio import refs_verdict
    assert refs_verdict.current(book) is not None
    assert refs.main([codex, "--chapter=1", "--cast=a"], conn=conn, **opts(tmp_path)) == 0
    assert db.get_codex(conn, codex)["refs_status"] == "completed"


def test_a_refusal_marks_the_stage_failed_and_raises(conn, tmp_path, book):
    codex = db.insert_codex(conn, "Book", codex_id="20260901000001")
    with pytest.raises(RuntimeError, match="--chapter"):
        refs.process(conn, codex, [], **opts(tmp_path))
    assert db.get_codex(conn, codex)["refs_status"] == "failed"
    assert db.unit_status(conn, codex, "refs", "main") == {"01": "failed"}
