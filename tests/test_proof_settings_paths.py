"""Every path of DESIGN 1.2 follows VISURENA_LIBRARY into a sandbox, and with the variable
unset every one is today's literal, byte for byte (2026-10-21_ep02_proof, P1).

Each mode runs in a child process: modules are imported there with the variable unset, then
the variable is set and settings plus every module are `importlib.reload`ed, so the pytest
process's own modules (and the exception classes other tests hold) are never replaced."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from studio import settings
from tests.proof_sandbox_fixture import env_for, tiny_sandbox

REPO = Path(__file__).resolve().parents[1]
MODULES = ["studio.episode_home", "studio.paths", "studio.db", "studio.comfy", "studio.engine_ops",
           "studio.take_phases", "studio.compute_device", "scripts.episode.gpu_ledger",
           "scripts.episode.autopilot", "scripts.episode.drive", "studio.plan_ladder", "studio.git_ahead",
           "scripts.episode.repair_dry_check", "scripts.episode.regress_delivered",
           "scripts.publish.youtube_auth"]

CHILD = r'''
import importlib, json, os, subprocess, sys, urllib.request
sys.path.insert(0, sys.argv[1])
modules = json.loads(sys.argv[2])
for name in modules:
    importlib.import_module(name)
os.environ.update(json.loads(sys.argv[3]))
from studio import settings
importlib.reload(settings)
m = {name.rsplit(".", 1)[1]: importlib.reload(importlib.import_module(name)) for name in modules}
cwds, urls = [], []
def run(argv, *a, **k):
    cwds.append(str(k.get("cwd")))
    return subprocess.CompletedProcess(argv, 0, "0\n", "")
subprocess.run = run
def urlopen(url, *a, **k):
    urls.append(url if isinstance(url, str) else url.full_url)
    raise OSError("no engine in this child")
urllib.request.urlopen = urlopen
m["autopilot"].git("rev-parse", "HEAD"); m["drive"].git("rev-parse", "HEAD")
m["plan_ladder"].code_sha8(); m["git_ahead"].commits_after("abc"); m["regress_delivered"].changed_paths()
m["repair_dry_check"].head_sha(); m["take_phases"].ring()
print(json.dumps({
    "LIBRARY": str(m["episode_home"].LIBRARY), "LIBRARY_ROOT": str(m["paths"].LIBRARY_ROOT),
    "DB_PATH": str(m["db"].DB_PATH), "COMFY_ROOT": str(m["comfy"].COMFY_ROOT), "HOST": m["comfy"].HOST,
    "VLM_CALLS": str(m["comfy"].VLM_CALLS), "TEXT_CACHE": str(m["comfy"].TEXT_CACHE),
    "ENGINE_HOST": m["engine_ops"].HOST, "DEFAULT_PORTABLE": m["engine_ops"].DEFAULT_PORTABLE,
    "CLAIMS": str(m["compute_device"].CLAIMS), "LOG": str(m["compute_device"].LOG),
    "LEDGER": str(m["gpu_ledger"].LEDGER), "LOCK": str(m["gpu_ledger"].LOCK),
    "AP_LIBRARY": str(m["autopilot"].LIBRARY), "ENGINE_URL": m["autopilot"].ENGINE_URL,
    "DEPS_ROOT": str(m["autopilot"].Deps().root), "PENDING": str(m["youtube_auth"].PENDING),
    "git_cwds": cwds, "urls": urls}))
'''


def constants(env: dict[str, str]) -> dict:
    """The constants and git cwds of every 1.2 module, as a child process sees them."""
    clean = {k: v for k, v in os.environ.items() if k not in ("VISURENA_LIBRARY", "COMFY_URL")}
    out = subprocess.run([sys.executable, "-c", CHILD, str(REPO), json.dumps(MODULES), json.dumps(env)],
                         capture_output=True, text=True, cwd=REPO, env=clean, timeout=180)
    assert out.returncode == 0, out.stderr[-3000:]
    return json.loads(out.stdout.strip().splitlines()[-1])


def test_unset_is_todays_literals_byte_for_byte():
    got = constants({})
    lib = REPO / "library"
    comfy = "D:/Projects/KingdomOfViSuReNa/alpha/ComfyUI_windows_portable/ComfyUI"
    assert got["LIBRARY"] == str(lib) == got["AP_LIBRARY"]
    assert got["LIBRARY_ROOT"] == str(Path("library"))
    assert got["DB_PATH"] == str(Path("db") / "visurena_studio.db")
    assert got["COMFY_ROOT"] == str(Path(comfy))
    assert got["HOST"] == got["ENGINE_HOST"] == got["ENGINE_URL"] == "http://127.0.0.1:8188"
    assert got["VLM_CALLS"] == str(lib / "vlm_calls.jsonl") and got["TEXT_CACHE"] == str(lib / ".vlm_cache")
    assert got["DEFAULT_PORTABLE"] == "D:/Projects/KingdomOfViSuReNa/alpha/ComfyUI_windows_portable"
    assert got["CLAIMS"] == str(lib / ".device" / "claims") and got["LOG"] == str(lib / ".device" / "decisions.jsonl")
    assert got["LEDGER"] == str(lib / ".device" / "gpu_util.jsonl") and got["LOCK"] == str(lib / ".autopilot" / "gpu.lock")
    assert got["DEPS_ROOT"] == str(lib / ".autopilot")
    assert got["PENDING"] == str(Path("library") / ".youtube_consent.json")
    assert got["git_cwds"] == [str(REPO)] * 6
    assert got["urls"] == ["http://127.0.0.1:8188/internal/logs/raw"]


def test_every_row_of_1_2_lands_in_the_sandbox(tmp_path):
    box = tiny_sandbox(tmp_path, comfy_host="http://127.0.0.1:18188")
    got, lib = constants(env_for(box)), box / "library"
    assert got["LIBRARY"] == got["AP_LIBRARY"] == got["LIBRARY_ROOT"] == str(lib)
    assert got["DB_PATH"] == str(box / "db" / "visurena_studio.db")
    assert got["COMFY_ROOT"] == str(box / "comfy")
    assert got["HOST"] == got["ENGINE_HOST"] == got["ENGINE_URL"] == "http://127.0.0.1:18188"
    assert got["VLM_CALLS"] == str(lib / "vlm_calls.jsonl") and got["TEXT_CACHE"] == str(lib / ".vlm_cache")
    assert Path(got["DEFAULT_PORTABLE"]).parent == box
    assert got["CLAIMS"] == str(lib / ".device" / "claims") and got["LOG"] == str(lib / ".device" / "decisions.jsonl")
    assert got["LEDGER"] == str(lib / ".device" / "gpu_util.jsonl") and got["LOCK"] == str(lib / ".autopilot" / "gpu.lock")
    assert got["DEPS_ROOT"] == str(lib / ".autopilot")
    assert got["PENDING"] == str(lib / ".youtube_consent.json")
    assert got["git_cwds"] == [str(box / "git")] * 6
    assert got["urls"] == ["http://127.0.0.1:18188/internal/logs/raw"]


def test_comfy_url_still_moves_the_autopilot_engine_outside_a_rehearsal():
    assert settings.comfy_host("http://box:9000", env={}) == "http://box:9000"
    assert settings.comfy_host(env={}) == "http://127.0.0.1:8188"


def test_rehearsal_host_wins_over_comfy_url(tmp_path):
    box = tiny_sandbox(tmp_path, comfy_host="http://127.0.0.1:18188")
    assert settings.comfy_host("http://box:9000", env=env_for(box)) == "http://127.0.0.1:18188"


@pytest.mark.parametrize("fn", ["rehearsal", "sandbox", "tmp_root"])
def test_unset_has_no_rehearsal_and_no_sandbox(fn):
    assert getattr(settings, fn)(env={}) is None
    assert settings.real_roots(env={}) == ()


def test_rehearsal_real_roots_name_the_library_db_comfy_and_the_two_docs(tmp_path):
    box = tiny_sandbox(tmp_path)
    roots = settings.real_roots(env=env_for(box))
    want = {REPO / "library", REPO / "db", REPO / "docs" / "DECISIONS.md", REPO / "docs" / "episode_handbook.html",
            settings.TODAY_COMFY_ROOT, tmp_path / "real_library"}
    assert {Path(r) for r in roots} >= {p.resolve() for p in want}
    assert settings.tmp_root(env=env_for(box)) == box / "tmp"
    assert settings.git_root(env=env_for(box)) == box / "git"
