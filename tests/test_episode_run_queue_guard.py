"""F2 (ep10 synthesis): run.py refuses a GPU-touching stage while the queue has
work, stamps the refusal, and `--after` waits instead.

The subprocess and the queue are injected; nothing here launches a stage or
touches ComfyUI.
"""
import importlib.util
import json
from pathlib import Path

import pytest

from studio import episode_clock as ck

spec = importlib.util.spec_from_file_location(
    "episode_run", Path(__file__).resolve().parents[1] / "scripts" / "episode" / "run.py")
run = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run)


class Done:
    returncode = 0


@pytest.fixture
def book(tmp_path, monkeypatch):
    monkeypatch.setattr(ck.episode_home, "home", lambda b, n: tmp_path / f"ep{n:02d}")
    monkeypatch.setattr(run.episode_home, "book_dir", lambda book_id: tmp_path)
    return tmp_path


@pytest.fixture
def launched(monkeypatch):
    calls = []

    def fake_run(cmd, **kw):
        calls.append(cmd)
        return Done()
    monkeypatch.setattr(run.subprocess, "run", fake_run)
    return calls


def test_a_gpu_stage_is_refused_while_the_queue_is_busy(book, launched):
    code = run.run("book", 10, "take_dq", [], busy=lambda: True)
    assert code != 0 and launched == []
    (row,) = ck.rows(book, 10)
    assert row["ok"] is False and row["note"] == "refused: queue busy"
    assert row["stage"] == "take_dq" and row["seconds"] == 0


def test_every_gpu_touching_stage_is_guarded():
    assert run.GPU_STAGES == {"lines", "frames", "takes", "title", "take_dq", "qc", "assemble"}


def test_a_cpu_stage_runs_while_the_queue_is_busy(book, launched):
    assert run.run("book", 10, "respot", [], busy=lambda: True) == 0
    assert len(launched) == 1 and ck.rows(book, 10)[0]["ok"] is True


def test_an_idle_queue_lets_the_stage_run(book, launched):
    assert run.run("book", 10, "takes", ["--approved"], busy=lambda: False) == 0
    assert launched[0][-1] == "--approved"


def test_after_waits_for_the_queue_then_runs(book, launched, monkeypatch):
    """The guard asks once; the wait asks again after every poll: three busy
    answers are two sleeps."""
    answers = iter([True, True, True, False])
    slept = []
    monkeypatch.setattr(run.time, "sleep", slept.append)
    code = run.run("book", 10, "qc", [], busy=lambda: next(answers), after=True)
    assert code == 0 and len(launched) == 1
    assert slept == [run.WAIT_POLL, run.WAIT_POLL]
    assert ck.rows(book, 10)[-1]["ok"] is True


def test_after_gives_up_at_the_cap_and_refuses(book, launched, monkeypatch):
    slept = []
    monkeypatch.setattr(run.time, "sleep", slept.append)
    code = run.run("book", 10, "qc", [], busy=lambda: True, after=True)
    assert code != 0 and launched == []
    assert sum(slept) >= run.WAIT_CAP
    assert ck.rows(book, 10)[-1]["note"] == "refused: queue busy"


def test_the_why_of_a_retake_lands_in_the_clock_note(book, launched):
    extra = ["--retake=3,15", "--why=T15 coherence 0.45 HARD; T03 chimney", "--approved"]
    run.run("book", 10, "takes", extra, busy=lambda: False)
    assert "--why=T15 coherence 0.45 HARD; T03 chimney" in ck.rows(book, 10)[0]["note"]


def test_main_strips_after_before_handing_the_stage_its_args(book, launched):
    run.main(["run.py", "book", "10", "qc", "--after", "--engine=r2v"], busy=lambda: False)
    assert "--after" not in launched[0] and "--engine=r2v" in launched[0]
