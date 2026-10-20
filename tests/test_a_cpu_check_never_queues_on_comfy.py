"""The CPU lane's take_dq runs WHILE the takes render (decision
2026-10-14-gpu-never-waits-for-checks).  takes_r2v queues every take on ComfyUI
in one go, so a check that put a job on ComfyUI -- the DINO leak embed, when its
workflow is installed -- would wait behind every render, and its model load
would evict the video weights between takes.  `--cpu-only` reads the leak
with the embedder-free step measure and marks the row DEFERRED; the GPU window
after the renders measures that take again with the embedder.  With no
embedder installed (production today), nothing is deferred: the verdict is
the one a serial run writes."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


take_dq = load("take_dq_cpu", "scripts/episode/take_dq.py")
step09 = load("step09_cpu", "scripts/episode/step_09_shoot.py")


def test_cpu_only_defers_the_leak_when_an_embedder_is_installed(monkeypatch):
    monkeypatch.setattr(take_dq, "embedder", lambda: ("embed", Path("in")))
    assert take_dq.judge_embedder(cpu_only=True) == (None, None, ["leak"])
    assert take_dq.judge_embedder(cpu_only=False) == ("embed", Path("in"), [])


def test_with_no_embedder_installed_nothing_is_deferred(monkeypatch):
    monkeypatch.setattr(take_dq, "embedder", lambda: (None, None))
    assert take_dq.judge_embedder(cpu_only=True) == (None, None, [])


def take_with_report(tmp_path: Path, **extra) -> Path:
    take = tmp_path / "T03.mp4"
    take.write_bytes(b"bytes of T03")
    report = take_dq.cache_key({}, take) | extra
    (tmp_path / "T03.dq.json").write_text(json.dumps(report), encoding="utf-8")
    return take


def test_a_deferred_verdict_is_never_served_from_the_cache(tmp_path):
    take = take_with_report(tmp_path, deferred=["leak"])
    assert take_dq.cached(tmp_path, 3, take) is None
    take = take_with_report(tmp_path)
    assert take_dq.cached(tmp_path, 3, take) is not None


def test_a_deferred_verdict_is_not_current_for_step_09(tmp_path):
    take = take_with_report(tmp_path, deferred=["leak"])
    assert not step09.dq_current(take)
    take = take_with_report(tmp_path)
    assert step09.dq_current(take)
