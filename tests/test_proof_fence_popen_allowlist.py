"""The launch fence: a process allowlist, refused BEFORE the spawn (DESIGN 2.6, R8, R19).

Allowed: ffmpeg/ffprobe (no output under a real root), git only at <sandbox>/git,
`uv run --no-sync python` from the repo, and sys.executable.  Everything else trips by
name: notify_bench.py (R8's DRIVE_QUIET=0 test), gpu_ledger.py (R19), claude, powershell,
schtasks and the portable python."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from studio.rehearsal import fence

REPO = Path(__file__).resolve().parents[1]
PORTABLE_PY = "D:/Projects/KingdomOfViSuReNa/alpha/ComfyUI_windows_portable/python_embeded/python.exe"


@pytest.fixture
def guard(tmp_path):
    lib, box = tmp_path / "real_library", tmp_path / "box"
    (box / "git").mkdir(parents=True)
    lib.mkdir()
    armed = fence.Fence.of(roots=(lib,), sandbox=box, repo=REPO)
    yield armed, lib, box
    fence.disarm()


@pytest.fixture
def child_env(monkeypatch):
    """This process's env as a rehearsal leaves it: the variable set, the boot first on PYTHONPATH."""
    monkeypatch.setenv("VISURENA_LIBRARY", "C:/sb/library")
    monkeypatch.setenv("PYTHONPATH", str(fence.BOOT))


def refusal(armed, argv, cwd=None, executable=None):
    return fence.launch_refusal(armed, executable, argv, cwd)


def test_a_python_child_inheriting_an_env_that_cannot_arm_it_trips(guard, monkeypatch):
    monkeypatch.delenv("VISURENA_LIBRARY", raising=False)
    monkeypatch.setenv("PYTHONPATH", str(fence.BOOT))
    assert "unfenced" in refusal(guard[0], [sys.executable, "-c", "pass"])
    monkeypatch.setenv("VISURENA_LIBRARY", "C:/sb/library")
    monkeypatch.setenv("PYTHONPATH", "C:/elsewhere")
    assert "unfenced" in refusal(guard[0], ["uv", "run", "--no-sync", "python", "w.py"], cwd=REPO)


def test_the_allowlist_passes_its_four_shapes(guard, child_env):
    armed, lib, box = guard
    assert refusal(armed, ["ffmpeg", "-y", "-i", str(lib / "in.mp4"), str(box / "out.mp4")]) is None
    assert refusal(armed, ["ffprobe", "-v", "error", str(lib / "in.mp4")]) is None
    assert refusal(armed, ["git", "rev-parse", "HEAD"], cwd=box / "git") is None
    assert refusal(armed, ["git", "-C", str(box / "git"), "status", "--porcelain"]) is None
    assert refusal(armed, ["uv", "run", "--no-sync", "python", "episode.py", "9999", "2"], cwd=REPO) is None
    assert refusal(armed, [sys.executable, "-c", "pass"]) is None


def test_a_windows_command_line_string_is_read_like_a_list(guard):
    armed, lib, box = guard
    assert refusal(armed, f'ffmpeg -y -i "{lib / "in.mp4"}" "{box / "o.mp4"}"') is None
    assert "gpu_ledger.py" in refusal(armed, 'uv run --no-sync python scripts/episode/gpu_ledger.py', cwd=REPO)


@pytest.mark.parametrize("argv, cwd, word", [
    (["uv", "run", "--no-sync", "python", "scripts/episode/gpu_ledger.py"], REPO, "gpu_ledger.py"),
    (["uv", "run", "--no-sync", "python", "D:/x/scripts/notify_bench.py", "text"], None, "notify_bench.py"),
    (["claude", "-p", "hi"], None, "claude"),
    (["powershell", "-NoProfile", "-Command", "Get-Process"], None, "powershell"),
    (["schtasks", "/query", "/tn", "visurena-autopilot"], None, "schtasks"),
    ([PORTABLE_PY, "-s", "ComfyUI/main.py"], None, "python"),
    (["git", "status", "--porcelain"], REPO, "git"),
    (["uv", "run", "--no-sync", "python", "episode.py"], Path("C:/elsewhere"), "uv"),
    (["uv", "sync"], REPO, "uv"),
])
def test_everything_else_trips_by_name(guard, argv, cwd, word):
    assert word in refusal(guard[0], argv, cwd=cwd)


def test_an_ffmpeg_output_under_a_real_root_trips(guard):
    armed, lib, box = guard
    assert "ffmpeg output" in refusal(armed, ["ffmpeg", "-i", str(box / "a.mp4"), str(lib / "out.mp4")])
    assert "ffprobe output" in refusal(armed, ["ffprobe", "-o", str(lib / "x.json"), str(box / "a.mp4")])


def trips(box: Path) -> list[dict]:
    path = box / "tripwire.jsonl"
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []


def test_drive_quiet_0_trips_on_notify_bench(guard, monkeypatch):
    from scripts.episode import drive
    armed, _, box = guard
    monkeypatch.setenv("DRIVE_QUIET", "0")
    fence.install(armed)
    with pytest.raises(fence.RehearsalTripwire, match="notify_bench.py"):
        drive.notify("rehearsal line")
    assert trips(box)[-1]["event"] == "subprocess.Popen"


def test_the_autopilot_gpu_ledger_launch_trips(guard, monkeypatch):
    from scripts.episode import autopilot
    armed, _, box = guard
    monkeypatch.setattr(autopilot.procs, "list_processes", lambda: [])
    fence.install(armed)
    with pytest.raises(fence.RehearsalTripwire, match="gpu_ledger.py"):
        autopilot.start_ledger()
    assert "gpu_ledger.py" in trips(box)[-1]["reason"]


def test_an_allowed_python_child_arms_itself_and_os_system_trips(guard, tmp_path, monkeypatch):
    from studio.rehearsal import activate
    from tests.proof_sandbox_fixture import tiny_sandbox
    armed, _, box = guard
    sb = tiny_sandbox(tmp_path / "sb")
    monkeypatch.setenv("VISURENA_LIBRARY", str(sb / "library"))
    monkeypatch.setenv("PYTHONPATH", str(fence.BOOT))
    monkeypatch.setenv(activate.CLEARED, f"{int(time.time())}|{sb}")     # the parent's verdict
    fence.install(armed)
    probe = "from studio.rehearsal import fence; print(fence.armed() is not None)"
    out = subprocess.run([sys.executable, "-c", probe], capture_output=True, text=True, timeout=120, cwd=tmp_path)
    assert out.stdout.strip() == "True", out.stderr[-1500:]
    with pytest.raises(fence.RehearsalTripwire):
        os.system("echo hi")
    assert [t["event"] for t in trips(box)] == ["os.system"]


@pytest.mark.parametrize("flags", [["-I"], ["-E"], ["-S"], ["-X", "utf8", "-I"], ["-sE"]])
def test_an_isolated_python_child_would_skip_the_boot_and_trips(guard, flags):
    armed = guard[0]
    assert "isolated" in refusal(armed, [sys.executable, *flags, "-c", "pass"])
    assert "isolated" in refusal(armed, ["uv", "run", "--no-sync", "python", *flags, "w.py"], cwd=REPO)


def test_python_flags_that_keep_the_boot_pass(guard, child_env):
    armed = guard[0]
    assert refusal(armed, [sys.executable, "-u", "-X", "utf8", "-c", "pass"]) is None
    assert refusal(armed, [sys.executable, "-m", "pytest", "-I"]) is None     # -I after -m is pytest's


def test_a_python_child_given_an_env_without_the_rehearsal_trips(guard, monkeypatch):
    armed = guard[0]
    boot = str(fence.BOOT)
    monkeypatch.setenv("VISURENA_LIBRARY", "C:/sb/library")
    keeps = {"VISURENA_LIBRARY": "C:/sb/library", "PYTHONPATH": boot}
    assert fence.launch_refusal(armed, None, [sys.executable, "-c", "pass"], None, keeps) is None
    for env in ({"PYTHONPATH": boot}, {"VISURENA_LIBRARY": "C:/sb/library"}, {}):
        assert "env" in fence.launch_refusal(armed, None, [sys.executable, "-c", "pass"], None, env)
    assert fence.launch_refusal(armed, None, ["ffmpeg", "-version"], None, {}) is None
