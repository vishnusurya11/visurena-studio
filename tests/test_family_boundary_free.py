"""The step runner frees the engine's models when the GPU model family changes (K10, P12)."""
import types

import pytest

from studio import comfy, db, step_runner
from studio.stage_run import StageContext


@pytest.fixture()
def conn(tmp_path):
    connection = db.get_connection(tmp_path / "t.db")
    db.init_db(connection)
    return connection


def _ctx(conn, tmp_path):
    codex_id = db.insert_codex(conn, "Book", codex_id="20260901000001")
    return StageContext(conn, codex_id, tmp_path / "book", "episode", unit="ep01", number=1,
                        logs_root=tmp_path / "logs", busy=lambda: False,
                        hold=tmp_path / "RENDER_HOLD", launch=lambda cmd: 0)


def _step(step_id, gpu=True):
    return types.SimpleNamespace(STEP_ID=step_id, NAME="x", GPU=gpu, run=lambda c: None,
                                 done=lambda c: False)


@pytest.fixture()
def freed(monkeypatch):
    calls = []
    monkeypatch.setattr(comfy, "free_on_family", lambda fam: calls.append(fam) or True)
    return calls


def test_a_different_family_frees_once(conn, tmp_path, freed, monkeypatch):
    fams = {"03": "image", "07": "image", "08": "vl", "09": "video"}
    monkeypatch.setattr(step_runner.step_caps, "family", lambda sid, stage="episode": fams[sid])
    step_runner.run_steps(_ctx(conn, tmp_path), [_step("03"), _step("07"), _step("08"), _step("09")])
    assert freed == ["image", "vl", "video"]                 # 07 is the same family as 03: none


def test_an_unknown_family_and_a_cpu_step_free_nothing(conn, tmp_path, freed, monkeypatch):
    monkeypatch.setattr(step_runner.step_caps, "family", lambda sid, stage="episode": "none")
    step_runner.run_steps(_ctx(conn, tmp_path), [_step("05", gpu=False), _step("10")])
    assert freed == []


def test_a_failed_free_does_not_fail_the_step(conn, tmp_path, monkeypatch):
    def boom(fam):
        raise OSError("engine down")
    monkeypatch.setattr(comfy, "free_on_family", boom)
    monkeypatch.setattr(step_runner.step_caps, "family", lambda sid, stage="episode": "vl")
    assert step_runner.run_steps(_ctx(conn, tmp_path), [_step("08")]) == "completed"
