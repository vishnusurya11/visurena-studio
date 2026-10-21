"""The fakes ride every rehearsal process (DESIGN 2.3; 2026-10-21_ep02_proof P4): activate.install()
calls fakes.install(manifest) in each one, and a Python child started with the sandbox env arms
itself through the rehearsal boot, so its brain client, its worker argv, its YouTube send and
its notify are the fakes too.  Also the patch helpers every fake module stands on."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import types
from pathlib import Path

import pytest

from studio.rehearsal import activate, fakes, fence
from tests.proof_sandbox_fixture import env_for, tiny_sandbox

REPO = Path(__file__).resolve().parents[1]
PROBE = """
import json
from studio import brain, face_detect, routed_whisper
from scripts.publish import youtube_upload
print(json.dumps({"client": brain.ClaudeSDKClient.__name__,
                  "detect": next(a for a in face_detect.worker_argv("p", "w", "cpu") if a.endswith(".py")),
                  "whisper": next(a for a in routed_whisper.worker_argv("p", "m", "r") if a.endswith(".py")),
                  "send": youtube_upload.send.__module__,
                  "upscale": __import__("os").environ.get("VISURENA_MASTER_UPSCALE")}))
"""


def child_env(box: Path) -> dict:
    """The sandbox env a rehearsal hands its children: the library, the boot first, the verdict."""
    env = {k: v for k, v in os.environ.items() if k not in ("VISURENA_LIBRARY", "PYTHONPATH")}
    return {**env, **env_for(box), "PYTHONPATH": str(fence.BOOT),
            activate.CLEARED: f"{int(time.time())}|{box}"}


def test_a_child_started_with_the_sandbox_env_carries_the_fakes(tmp_path):
    box = tiny_sandbox(tmp_path, fakes=True)
    out = subprocess.run([sys.executable, "-c", PROBE], cwd=REPO, env=child_env(box), capture_output=True,
                         text=True, timeout=120)
    assert out.returncode == 0, out.stderr[-2000:]
    got = json.loads(out.stdout.strip().splitlines()[-1])
    assert got["client"] == "RehearsalClient" and got["upscale"] == "lanczos"
    assert Path(got["detect"]).name == "fake_detect_worker.py"
    assert Path(got["whisper"]).name == "fake_whisper_worker.py"
    assert got["send"] == "studio.rehearsal.fake_publish"
    assert not (box / "tripwire.jsonl").exists()


EAR = """
import json, sys
from pathlib import Path
from studio import routed_whisper
worker = routed_whisper.Worker(routed_whisper.spawn_worker(None))
print(json.dumps({"heard": worker(Path(sys.argv[1]))}))
worker.close()
"""


def test_a_fake_worker_spawned_inside_a_fenced_rehearsal_arms_and_answers(tmp_path):
    from studio.rehearsal import fake_workers
    box = tiny_sandbox(tmp_path, fakes=True)
    wav = box / "tmp" / "line01.wav"
    wav.write_bytes(b"recorded line")
    (box / "memos").mkdir()
    (box / "memos" / "whisper.json").write_text(json.dumps({fake_workers.file_key(wav): "heard it"}), encoding="utf-8")
    out = subprocess.run([sys.executable, "-c", EAR, str(wav)], cwd=REPO, env=child_env(box), capture_output=True,
                         text=True, timeout=120)
    assert out.returncode == 0, out.stderr[-2000:]
    assert json.loads(out.stdout.strip().splitlines()[-1]) == {"heard": "heard it"}
    assert not (box / "tripwire.jsonl").exists()
    assert any(json.loads(x).get("label") == "exact" for x in (box / "workers.jsonl").read_text(encoding="utf-8").splitlines())


def test_a_child_outside_a_rehearsal_has_none_of_them(tmp_path):
    env = {k: v for k, v in os.environ.items() if k not in ("VISURENA_LIBRARY", "PYTHONPATH")}
    out = subprocess.run([sys.executable, "-c", PROBE], cwd=REPO, env=env, capture_output=True, text=True, timeout=120)
    got = json.loads(out.stdout.strip().splitlines()[-1])
    assert got["client"] == "ClaudeSDKClient" and Path(got["detect"]).name == "face_detect_worker.py"


# ---- the helpers ----------------------------------------------------------------------

@pytest.fixture
def live(tmp_path):
    fakes.install({}, tmp_path)
    yield tmp_path
    fakes.uninstall()


def test_a_rebind_lands_when_its_module_is_imported_and_is_undone(live, monkeypatch):
    name = "studio_rehearsal_probe_mod"
    mod = types.ModuleType(name)
    mod.value = 21
    monkeypatch.setitem(sys.modules, name, mod)
    fakes.rebind(name, "value", lambda old: old + 1)
    assert mod.value == 22
    fakes.uninstall()
    assert mod.value == 21


def test_a_patch_pending_from_an_earlier_install_never_lands(tmp_path, monkeypatch):
    fakes.install({}, tmp_path)
    fakes.on_import("studio_rehearsal_never_imported", lambda m: pytest.fail("a stale patch landed"))
    fakes.uninstall()
    mod = types.ModuleType("studio_rehearsal_never_imported")
    for patch in fence._PENDING.pop("studio_rehearsal_never_imported", []):
        patch(mod)


def test_set_default_rebinds_positional_and_keyword_only_defaults():
    def f(a, b=1, *, c=2):
        return a, b, c
    undo_b, undo_c = fakes.set_default(f, "b", 10), fakes.set_default(f, "c", 20)
    assert f(0) == (0, 10, 20)
    undo_c(), undo_b()
    assert f(0) == (0, 1, 2)


def test_a_log_row_lands_in_the_sandbox(live):
    fakes.log(live, "probe", {"x": 1})
    row = json.loads((live / "probe.jsonl").read_text(encoding="utf-8"))
    assert row["x"] == 1 and row["pid"] == os.getpid()


def test_installing_without_a_sandbox_refuses(monkeypatch):
    monkeypatch.delenv("VISURENA_LIBRARY", raising=False)
    with pytest.raises(RuntimeError, match="sandbox"):
        fakes.install({})


def test_activate_loads_these_fakes(tmp_path, monkeypatch):
    seen = []
    monkeypatch.setattr(fakes, "install", lambda manifest, box=None: seen.append(manifest))
    activate.load_fakes({"fakes": True, "scale": 1})
    assert seen == [{"fakes": True, "scale": 1}]
