"""The four fail-closed refusals of DESIGN 1.1 (2026-10-21_ep02_proof, P1, R18):
the variable without a manifest; a manifest whose sandbox touches a real root; a manifest
naming :8188; and a rehearsal while the real task is enabled or a real series is unpaused.
The scheduler and the series are faked here; nothing reads or writes the real library."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from studio import settings
from studio.rehearsal import activate, fence
from tests.proof_sandbox_fixture import env_for, tiny_sandbox

REPO = Path(__file__).resolve().parents[1]
SCHTASKS_READY = '"TaskName","Next Run Time","Status"\n"\\visurena-autopilot","10/21/2026 8:20:00 AM","Ready"\n'
SCHTASKS_OFF = '"TaskName","Next Run Time","Status"\n"\\visurena-autopilot","N/A","Disabled"\n'


def manifest_at(box: Path, **fields) -> dict[str, str]:
    (box / "library").mkdir(parents=True, exist_ok=True)
    (box / "rehearsal.json").write_text(json.dumps(fields), encoding="utf-8")
    return env_for(box)


def test_the_variable_without_a_manifest_raises(tmp_path):
    with pytest.raises(settings.RehearsalEnvLeak):
        settings.rehearsal(env={"VISURENA_LIBRARY": str(tmp_path / "library")})


def test_import_studio_with_a_leaked_variable_fails_every_entry_point(tmp_path):
    env = {**os.environ, "VISURENA_LIBRARY": str(tmp_path / "library")}
    out = subprocess.run([sys.executable, "-c", "import studio"], cwd=REPO, env=env,
                         capture_output=True, text=True, timeout=60)
    assert out.returncode != 0 and "RehearsalEnvLeak" in out.stderr


def test_a_sandbox_touching_a_real_root_raises(tmp_path):
    real = tmp_path / "real_library"
    env = manifest_at(real / "sub", real_library=str(real))
    with pytest.raises(settings.RehearsalManifestUnsafe):
        settings.rehearsal(env=env)


def test_a_sandbox_that_holds_a_real_root_raises(tmp_path):
    env = manifest_at(tmp_path, real_library=str(tmp_path / "inner" / "library"))
    with pytest.raises(settings.RehearsalManifestUnsafe):
        settings.rehearsal(env=env)


def test_the_repo_itself_as_sandbox_raises():
    assert settings.overlaps(REPO, REPO / "db") and settings.overlaps(REPO / "library" / "x", REPO / "library")
    assert not settings.overlaps(REPO / "docs" / "audit" / "sandbox", REPO / "library")


@pytest.mark.parametrize("fields", [{"comfy_host": "http://127.0.0.1:8188"}, {"fake_ports": [8188]},
                                    {"comfy_host": "http://localhost:8188/"}])
def test_a_manifest_naming_the_real_engine_port_raises(tmp_path, fields):
    with pytest.raises(settings.RehearsalManifestUnsafe):
        settings.rehearsal(env=manifest_at(tmp_path / "box", **fields))


def test_a_sound_manifest_loads(tmp_path):
    box = tiny_sandbox(tmp_path, comfy_host="http://127.0.0.1:18188")
    assert settings.rehearsal(env=env_for(box))["comfy_host"] == "http://127.0.0.1:18188"


def test_the_scheduler_csv_reads_as_enabled_or_disabled():
    assert activate.task_enabled(SCHTASKS_READY) and not activate.task_enabled(SCHTASKS_OFF)
    assert not activate.task_enabled("")


def test_unpaused_series_are_found_one_level_deep(tmp_path):
    lib = tmp_path / "library"
    for book, doc in (("a_book", {"paused": False}), ("b_book", {"paused": True}), ("c_book", {"paused": False})):
        (lib / book / "autopilot").mkdir(parents=True)
        (lib / book / "autopilot" / "series.json").write_text(json.dumps(doc), encoding="utf-8")
    (lib / "c_book" / "autopilot" / "STOP").write_text("", encoding="utf-8")
    assert [p.parts[-3] for p in activate.unpaused_series(lib)] == ["a_book"]


def armed_calls(monkeypatch) -> list:
    calls: list = []
    monkeypatch.setattr(fence, "install", lambda *a, **k: calls.append("fence"))
    monkeypatch.setattr(activate, "_INSTALLED", False)
    monkeypatch.setattr(activate, "arm_children", lambda: None)
    monkeypatch.setattr(activate, "mark_cleared", lambda box: None)
    return calls


def test_an_enabled_task_refuses_before_the_fence(tmp_path, monkeypatch):
    box, calls = tiny_sandbox(tmp_path), armed_calls(monkeypatch)
    manifest = settings.rehearsal(env=env_for(box))
    with pytest.raises(activate.RehearsalRefused, match="visurena-autopilot"):
        activate.install(manifest, env=env_for(box), schtasks=lambda: SCHTASKS_READY, series=lambda: [])
    assert calls == []


def test_an_unpaused_real_series_refuses_before_the_fence(tmp_path, monkeypatch):
    box, calls = tiny_sandbox(tmp_path), armed_calls(monkeypatch)
    manifest = settings.rehearsal(env=env_for(box))
    with pytest.raises(activate.RehearsalRefused, match="unpaused"):
        activate.install(manifest, env=env_for(box), schtasks=lambda: SCHTASKS_OFF,
                         series=lambda: [Path("library/x/autopilot/series.json")])
    assert calls == []


def test_missing_fakes_refuse_unless_the_manifest_says_none(tmp_path, monkeypatch):
    box, calls = tiny_sandbox(tmp_path, fakes=True), armed_calls(monkeypatch)
    monkeypatch.setattr(activate, "module_present", lambda name: False)
    monkeypatch.setattr(activate, "point_tempdir", lambda box: None)
    manifest = settings.rehearsal(env=env_for(box))
    with pytest.raises(activate.RehearsalRefused, match="fakes"):
        activate.install(manifest, env=env_for(box), schtasks=lambda: SCHTASKS_OFF, series=lambda: [])
    monkeypatch.setattr(activate, "_INSTALLED", False)
    assert activate.install({**manifest, "fakes": False}, env=env_for(box),
                            schtasks=lambda: SCHTASKS_OFF, series=lambda: []) is True


def test_no_manifest_installs_nothing(monkeypatch):
    calls = armed_calls(monkeypatch)
    assert activate.install(env={}) is False and calls == []


def test_studio_init_carries_the_one_install_line():
    lines = (REPO / "studio" / "__init__.py").read_text(encoding="utf-8").splitlines()
    assert [ln for ln in lines if "activate" in ln] == [
        "from studio.rehearsal import activate as _activate; _activate.install()  # no-op without a manifest"]


def fake_run(monkeypatch, returncode: int, stdout: str = "", stderr: str = "") -> list:
    seen: list = []

    def run(argv, **kw):
        seen.append(argv)
        return subprocess.CompletedProcess(argv, returncode, stdout, stderr)
    monkeypatch.setattr(activate.subprocess, "run", run)
    return seen


def test_the_scheduler_query_is_read_only(monkeypatch):
    seen = fake_run(monkeypatch, 0, SCHTASKS_READY)
    assert activate.schtasks_query() == SCHTASKS_READY
    assert seen == [["schtasks", "/query", "/tn", "visurena-autopilot", "/fo", "csv"]]


def test_a_missing_task_is_a_definite_no(monkeypatch):
    fake_run(monkeypatch, 1, stderr="ERROR: The system cannot find the file specified.\n")
    assert activate.schtasks_query() == ""


@pytest.mark.parametrize("failure", ["exit", "oserror", "timeout"])
def test_a_scheduler_that_cannot_say_is_none(monkeypatch, failure):
    if failure == "exit":
        fake_run(monkeypatch, 1, stderr="ERROR: Access is denied.\n")
    else:
        err = OSError("no schtasks") if failure == "oserror" else subprocess.TimeoutExpired("schtasks", 30)
        monkeypatch.setattr(activate.subprocess, "run", lambda *a, **k: (_ for _ in ()).throw(err))
    assert activate.schtasks_query() is None


def test_cannot_say_refuses_the_rehearsal(tmp_path, monkeypatch):
    box, calls = tiny_sandbox(tmp_path), armed_calls(monkeypatch)
    manifest = settings.rehearsal(env=env_for(box))
    with pytest.raises(activate.RehearsalRefused, match="cannot read"):
        activate.install(manifest, env=env_for(box), schtasks=lambda: None, series=lambda: [])
    assert calls == []


def test_a_child_inherits_its_parents_clearance_and_skips_the_query(tmp_path, monkeypatch):
    box = tiny_sandbox(tmp_path)
    monkeypatch.setenv(activate.CLEARED, "")
    activate.mark_cleared(box)
    env = {**env_for(box), activate.CLEARED: os.environ[activate.CLEARED]}
    assert activate.cleared(env, box) and not activate.cleared(env, tmp_path / "other")
    stale = {**env, activate.CLEARED: f"{time.time() - activate.CLEARANCE_S - 5:.0f}|{box}"}
    assert not activate.cleared(stale, box) and not activate.cleared({**env, activate.CLEARED: "junk"}, box)
    calls = armed_calls(monkeypatch)
    monkeypatch.setattr(activate, "point_tempdir", lambda box: None)
    activate.install(settings.rehearsal(env=env), env=env, schtasks=lambda: SCHTASKS_READY, series=lambda: [])
    assert calls == ["fence"]


def test_arm_children_puts_the_boot_path_first(tmp_path, monkeypatch):
    monkeypatch.setenv("PYTHONPATH", "C:/elsewhere")
    activate.arm_children()
    assert os.environ["PYTHONPATH"].split(os.pathsep) == [str(fence.BOOT), "C:/elsewhere"]
    activate.arm_children()
    assert os.environ["PYTHONPATH"].split(os.pathsep).count(str(fence.BOOT)) == 1
    assert (fence.BOOT / "sitecustomize.py").is_file()


def test_point_tempdir_sends_temp_files_into_the_sandbox(tmp_path, monkeypatch):
    import tempfile
    monkeypatch.setattr(tempfile, "tempdir", tempfile.tempdir)
    for name in ("TMP", "TEMP"):
        monkeypatch.setenv(name, os.environ.get(name, ""))
    activate.point_tempdir(tmp_path)
    assert tempfile.gettempdir() == str(tmp_path / "tmp") == os.environ["TMP"] == os.environ["TEMP"]


def test_fake_ports_and_the_comfy_paths_follow_the_manifest(tmp_path):
    box = tiny_sandbox(tmp_path, comfy_host="http://127.0.0.1:18188", fake_ports=[18190])
    env = env_for(box)
    assert settings.fake_ports(env=env) == (18188, 18190) and settings.fake_ports(env={}) == ()
    assert settings.comfy_root(env=env) == box / "comfy" and settings.comfy_root(env={}) == settings.TODAY_COMFY_ROOT
    assert settings.comfy_portable(env={}) == settings.TODAY_PORTABLE
    assert settings.db_path(env=env) == box / "db" / "visurena_studio.db"
    assert settings.real_libraries(env={}) == (settings.REAL_LIBRARY,)
