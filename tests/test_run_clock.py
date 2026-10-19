"""run_clock.dead_gaps (K4): the time between runs, with the reason drive.jsonl gave (P12).
Built from the ep01 clock.jsonl / drive.jsonl copies."""
import json
import shutil
from pathlib import Path

from studio import run_clock

FIX = Path(__file__).parent / "fixtures" / "ep01_replay" / "P12"


def _home(tmp_path):
    for name in ("clock.jsonl", "drive.jsonl"):
        shutil.copy(FIX / name, tmp_path / name)
    return tmp_path


def test_dead_gaps_sum_from_the_runs(tmp_path):
    home = _home(tmp_path)
    gaps = run_clock.dead_gaps(home)
    runs = run_clock.rows(home)
    want = sum(b["started"] - a["ended"] for a, b in zip(runs, runs[1:]) if b["started"] > a["ended"])
    assert gaps and abs(sum(g["seconds"] for g in gaps) - want) < 0.5
    assert all(g["seconds"] > 0 and g["end"] > g["start"] for g in gaps)


def test_a_gap_carries_the_reason_drive_jsonl_gave(tmp_path):
    gaps = run_clock.dead_gaps(_home(tmp_path))
    assert gaps[0]["reason"].startswith("paused")            # run 1 ended `paused`
    assert all(isinstance(g["reason"], str) and g["reason"] for g in gaps)


def test_overlapping_runs_leave_no_gap(tmp_path):
    rows = [{"started": 0.0, "ended": 100.0}, {"started": 50.0, "ended": 200.0}, {"started": 260.0, "ended": 300.0}]
    (tmp_path / "clock.jsonl").write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    gaps = run_clock.dead_gaps(tmp_path)
    assert [(g["start"], g["end"], g["seconds"], g["reason"]) for g in gaps] == [(200.0, 260.0, 60.0, "unknown")]
