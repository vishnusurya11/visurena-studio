"""episode.py: the registry's ids are the modules' ids; every step runs alone
and answers --help; a finished unit is skipped step by step; an owner gate
exits 2 having marked nothing failed; a bare codex id finds every unit.

Nothing here launches a script, touches a GPU or reads the library.
"""
from __future__ import annotations

import subprocess
import sys
import types
from pathlib import Path

import pytest

import episode
from studio import db, episode_home, registry, step_runner

ROOT = Path(__file__).resolve().parents[1]
CODEX = "20260901000001"


@pytest.fixture(autouse=True)
def stub_step_02(monkeypatch):
    """Step 02 is written by another hand; when its file is absent the registry
    still has to resolve, so the import is answered by a stub."""
    name = "scripts.episode.step_02_plan"
    if not (ROOT / "scripts" / "episode" / "step_02_plan.py").exists():
        stub = types.ModuleType(name)
        stub.STEP_ID, stub.NAME, stub.GPU = "02", "plan", False
        stub.done, stub.run = (lambda ctx: True), (lambda ctx: None)
        monkeypatch.setitem(sys.modules, name, stub)


@pytest.fixture()
def conn(tmp_path):
    connection = db.get_connection(tmp_path / "t.db")
    db.init_db(connection)
    db.insert_codex(connection, "Book", codex_id=CODEX)
    return connection


@pytest.fixture()
def book(tmp_path, monkeypatch):
    monkeypatch.setattr(episode_home, "book_dir", lambda codex_id: tmp_path / "book")
    (tmp_path / "book").mkdir()
    return tmp_path / "book"


def _opts(tmp_path, launched=None):
    return dict(logs_root=tmp_path / "logs", busy=lambda: False, hold=tmp_path / "RENDER_HOLD",
                launch=lambda cmd: (launched.append(cmd) if launched is not None else None) or 0)


def test_the_registry_and_the_modules_agree_on_ids():
    steps = step_runner.load_steps("episode")
    assert [s.STEP_ID for s in steps] == [e["id"] for e in registry.steps("episode")]
    assert [s.NAME for s in steps] == [e["name"] for e in registry.steps("episode")]


def test_every_step_module_declares_the_contract():
    for step in step_runner.load_steps("episode"):
        assert isinstance(step.GPU, bool) and callable(step.run) and callable(step.done), step.STEP_ID


@pytest.mark.parametrize("entry", [e for e in registry.steps("episode") if e["id"] != "02"],
                         ids=lambda e: e["script"])
def test_every_step_answers_help_alone(entry):
    script = ROOT / "scripts" / "episode" / f"{entry['script']}.py"
    done = subprocess.run([sys.executable, str(script), "--help"], cwd=ROOT,
                          capture_output=True, text=True, encoding="utf-8", errors="replace")
    assert done.returncode == 0, done.stderr
    assert f"Step {entry['id']}" in done.stdout


def test_units_are_the_episode_folders_with_a_plan(book):
    for n, planned in ((3, True), (1, True), (2, False)):
        (book / "episodes" / f"ep{n:02d}").mkdir(parents=True)
        if planned:
            (book / "episodes" / f"ep{n:02d}" / "plan.json").write_text("{}", encoding="utf-8")
    assert episode.units(book) == [1, 3]
    assert episode.units(book / "nowhere") == []


def test_parse_reads_the_unit_and_keeps_the_flags():
    assert episode.parse([CODEX, "4", "--cast=a,b"]) == (CODEX, 4, ["--cast=a,b"])
    assert episode.parse([CODEX]) == (CODEX, None, [])
    with pytest.raises(SystemExit, match="usage"):
        episode.parse(["--only-flags"])


def test_preflight_refuses_a_missing_tool():
    with pytest.raises(SystemExit, match="no-such-tool"):
        episode.preflight(("no-such-tool-xyz",))


def test_a_finished_unit_skips_every_step(conn, book, tmp_path, monkeypatch):
    for step in step_runner.load_steps("episode"):
        monkeypatch.setattr(step, "done", lambda ctx: True)
    code = episode.main([CODEX, "1"], conn=conn, tools=(), **_opts(tmp_path))
    assert code == 0
    status = db.unit_status(conn, CODEX, "episode", "ep01")
    assert set(status.values()) == {"skipped"} and len(status) == len(registry.steps("episode"))
    assert db.get_codex(conn, CODEX)["episode_status"] == "completed"


def test_an_escalation_exits_2_and_marks_nothing_failed(conn, book, tmp_path, monkeypatch):
    from studio.escalate import Escalation
    steps = step_runner.load_steps("episode")
    monkeypatch.setattr(steps[0], "done", lambda ctx: False)

    def park(ctx):
        raise Escalation("PLAN", "plan.verdict.json", "sign the plan")
    monkeypatch.setattr(steps[0], "run", park)
    launched = []
    code = episode.main([CODEX, "1"], conn=conn, tools=(), **_opts(tmp_path, launched))
    assert code == 2 and launched == []
    status = db.unit_status(conn, CODEX, "episode", "ep01")
    assert status == {"01": "escalated"}
    assert db.get_codex(conn, CODEX)["episode_status"] != "failed"


def test_a_bare_codex_runs_every_planned_unit_in_order(conn, book, tmp_path, monkeypatch):
    for n in (2, 1):
        (book / "episodes" / f"ep{n:02d}").mkdir(parents=True)
        (book / "episodes" / f"ep{n:02d}" / "plan.json").write_text("{}", encoding="utf-8")
    seen = []
    for step in step_runner.load_steps("episode"):
        monkeypatch.setattr(step, "done", lambda ctx, s=step: seen.append((ctx.unit, s.STEP_ID)) or True)
    assert episode.main([CODEX], conn=conn, tools=(), **_opts(tmp_path)) == 0
    assert [u for u, _ in seen][:1] == ["ep01"] and [u for u, _ in seen][-1] == "ep02"


def test_a_book_with_no_planned_unit_is_refused(conn, book, tmp_path):
    with pytest.raises(SystemExit, match="plan.json"):
        episode.main([CODEX], conn=conn, tools=(), **_opts(tmp_path))


def test_the_flags_reach_the_step(conn, book, tmp_path, monkeypatch):
    steps = step_runner.load_steps("episode")
    got = {}
    for step in steps:
        monkeypatch.setattr(step, "done", lambda ctx: True)
    monkeypatch.setattr(steps[0], "done", lambda ctx: got.update(extra=list(ctx.extra)) or True)
    episode.main([CODEX, "1", "--cast=a,b"], conn=conn, tools=(), **_opts(tmp_path))
    assert got["extra"] == ["--cast=a,b"]
