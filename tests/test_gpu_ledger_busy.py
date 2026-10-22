"""A1 (fleet E, 2026-10-22): the ledger's busy rule and its unsampled bucket.

Idle util on this card reads a median 4 and a p90 6 with an empty queue and no claim
(library/.device/gpu_util.jsonl), so `util >= 5` called an idle card busy.  Busy is now
`queue_running > 0 or util >= 30` (99.3 % against ComfyUI job windows on 2,623 samples,
fleet E bench G1); a live claim at low util stays its own `claimed` line (skeptic M1), and
step time no sample covers is `unsampled`, never idle or busy."""
from __future__ import annotations

import importlib.util
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


def test_an_idle_card_at_util_6_is_idle_not_busy():
    assert load().kind({"gpu_util": 6, "queue_running": 0, "claims": 0}) == "idle"


def test_a_worker_at_low_util_holding_a_claim_is_claimed():
    assert load().kind({"gpu_util": 12, "queue_running": 0, "claims": 1}) == "claimed"


def test_a_running_queue_is_busy_whatever_the_util():
    assert load().kind({"gpu_util": 0, "queue_running": 1, "claims": 0}) == "busy"


def test_a_worker_at_util_30_is_busy():
    assert load().kind({"gpu_util": 30, "queue_running": 0, "claims": 1}) == "busy"


def test_a_hole_between_samples_is_unsampled():
    mod = load()
    rows = [{"ts": t, "gpu_util": 0, "queue_running": 0, "claims": 0} for t in (0, 5, 10)]   # 15 s sampled
    got = mod.minutes_per_step(rows, [("10", 0.0, 45.0)], every=5.0)                      # a 45 s step
    assert got["10"] == {"busy": 0.0, "claimed": 0.0, "idle": 0.25, "unsampled": 0.5}


def test_the_finish_report_names_the_unsampled_minutes(tmp_path):
    mod = load()
    (tmp_path / "timing.jsonl").write_text(
        '{"stage": "step_10", "seconds": 60, "ended": "2026-10-22T05:01:00"}\n', encoding="utf-8")
    rows = [{"ts": mod.step_spans(tmp_path)[0][1], "gpu_util": 0, "queue_running": 0, "claims": 0}]
    line = mod.finish_report(tmp_path, rows).splitlines()[-1]
    assert line == "  step 10: busy 0.0 | claimed 0.0 | idle 0.08 | unsampled 0.92 min"
