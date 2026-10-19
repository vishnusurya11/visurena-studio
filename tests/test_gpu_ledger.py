"""P13: the GPU/RAM ledger -- a 5 s sampler writing library/.device/gpu_util.jsonl.
Probes are injected; nothing here reaches nvidia-smi, ComfyUI or the process table."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load():
    if "gpu_ledger_cli" in sys.modules:
        return sys.modules["gpu_ledger_cli"]
    spec = importlib.util.spec_from_file_location("gpu_ledger_cli", ROOT / "scripts" / "episode" / "gpu_ledger.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["gpu_ledger_cli"] = mod
    spec.loader.exec_module(mod)
    return mod


def probes(mod, **over):
    base = dict(queue=lambda: {"running": 1, "pending": 2}, claims=lambda: [{"job": "whisper"}],
                smi=lambda: {"gpu_used_mib": 9000, "gpu_util": 71},
                host=lambda: {"commit_free_gb": 21.5, "ram_free_gb": 12.25},
                comfy_bytes=lambda: 5 * 2**30)
    return mod.Probes(**{**base, **over})


def test_a_sample_carries_every_field_the_brief_names():
    mod = load()
    row = mod.sample(probes(mod), 100.0)
    assert row == {"ts": 100.0, "queue_running": 1, "queue_pending": 2, "claims": 1, "gpu_used_mib": 9000,
                   "gpu_util": 71, "commit_free_gb": 21.5, "ram_free_gb": 12.25, "comfy_private_bytes": 5 * 2**30}


def test_a_probe_failure_writes_probe_error_and_continues():
    mod = load()

    def broken():
        raise OSError("nvidia-smi is gone")
    row = mod.sample(probes(mod, smi=broken), 100.0)
    assert row["probe_error"] == ["smi"] and row["queue_running"] == 1 and "gpu_util" not in row


def test_run_appends_one_row_per_tick_and_survives_a_failed_probe(tmp_path):
    mod = load()
    path = tmp_path / "gpu_util.jsonl"
    clock = iter(range(10))
    mod.run(path, probes(mod, queue=lambda: 1 / 0), now=lambda: float(next(clock)), sleep=lambda s: None, ticks=3)
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 3 and rows[0]["probe_error"] == ["queue"]


def test_run_stops_when_told_to(tmp_path):
    mod = load()
    seen = []
    mod.run(tmp_path / "g.jsonl", probes(mod), now=lambda: 1.0, sleep=lambda s: seen.append(s), ticks=None,
            stop=lambda: len(seen) >= 2)
    assert len((tmp_path / "g.jsonl").read_text(encoding="utf-8").splitlines()) == 2


def test_minutes_per_step_split_busy_idle_and_claimed():
    mod = load()
    rows = ([{"ts": t, "gpu_util": 80, "queue_running": 1, "claims": 0} for t in range(0, 60, 5)]      # 12 busy
            + [{"ts": t, "gpu_util": 0, "queue_running": 0, "claims": 1} for t in range(60, 120, 5)]  # 12 claimed
            + [{"ts": t, "gpu_util": 0, "queue_running": 0, "claims": 0} for t in range(120, 180, 5)])  # 12 idle
    got = mod.minutes_per_step(rows, [("09", 0.0, 90.0), ("10", 90.0, 180.0)], every=5.0)
    assert got["09"] == {"busy": 1.0, "claimed": 0.5, "idle": 0.0}
    assert got["10"] == {"busy": 0.0, "claimed": 0.5, "idle": 1.0}


def test_the_time_line_names_charged_wall_and_dead():
    mod = load()
    line = mod.time_line(charged_s=3 * 3600, wall_s=4 * 3600, dead_s=1800)
    assert line == "charged 3.00 h | wall 4.00 h | dead 0.50 h"
