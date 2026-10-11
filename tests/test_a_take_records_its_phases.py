"""R2_S #5 / R2_verdict §2.2: every take records its phases -- encode, the gap to
the first step, s/it, steps, sampling, decode+save, and whether the UNET or the
text encoder re-ran -- the clock for every speed claim and the tripwire.  The
sampler bar comes from ComfyUI's own timestamped log ring (/internal/logs/raw;
the live engine's comfyui.log was overwritten by a failed second launch), the
re-runs from the history's execution_cached list."""
from datetime import datetime

from studio import take_phases as tp


def ts(s: str) -> float:
    return datetime.fromisoformat(f"2026-10-11T{s}").timestamp()


ENTRIES = [
    {"t": "2026-10-11T01:00:00.000000", "m": "got prompt\n"},
    {"t": "2026-10-11T01:00:06.000000", "m": "Requested to load MiniMaxH3\n"},
    {"t": "2026-10-11T01:00:09.000000", "m": "\r  0%|          | 0/4 [00:00<?, ?it/s]"},
    {"t": "2026-10-11T01:00:30.000000", "m": "\r 50%|#####     | 2/4 [00:21<00:21, 10.5s/it]"},
    {"t": "2026-10-11T01:00:51.000000", "m": "\r100%|##########| 4/4 [00:42<00:00, 10.4s/it]"},
    {"t": "2026-10-11T01:00:51.000000", "m": "\rUSDU: 100%|####| 6/6 [00:07<00:00,  1.2s/tile]"},
]
RECORD = {"status": {"messages": [
    ["execution_start", {"timestamp": ts("01:00:00") * 1000}],
    ["execution_cached", {"nodes": ["5", "6", "7"]}],
    ["execution_success", {"timestamp": ts("01:01:05") * 1000}]]},
    "prompt": [0, "pid", {"1": {"class_type": "UNETLoader", "inputs": {}},
                          "5": {"class_type": "CLIPLoader", "inputs": {}}}]}


def test_the_phases_are_read_inside_the_takes_window():
    p = tp.phases(RECORD, ENTRIES)
    assert p["steps"] == 4 and p["s_per_it"] == 10.4 and p["sample_s"] == 42
    assert p["encode_s"] == 6.0 and p["first_step_gap_s"] == 3.0
    assert p["decode_save_s"] == 14.0 and p["prompt_s"] == 65.0


def test_the_reruns_come_from_the_cached_list():
    p = tp.phases(RECORD, ENTRIES)
    assert p["unet_reran"] is True and p["te_reran"] is False


def test_a_bar_in_it_per_second_is_turned_into_seconds_per_it():
    e = [{"t": "2026-10-11T01:00:20.000000", "m": "\r100%|####| 8/8 [00:06<00:00,  1.25it/s]"}]
    assert tp.phases(RECORD, e)["s_per_it"] == 0.8


def test_a_ring_that_lost_the_take_records_what_history_knows():
    p = tp.phases(RECORD, [])
    assert p["prompt_s"] == 65.0 and p["s_per_it"] is None and p["unet_reran"] is True


def test_the_row_lands_in_the_takes_phases_file(tmp_path):
    tp.record(tmp_path / "T03.mp4", {"index": 3}, RECORD, ENTRIES)
    import json
    row = json.loads((tmp_path / "phases.jsonl").read_text("utf-8").splitlines()[0])
    assert row["take"] == 3 and row["steps"] == 4


def test_the_take_step_writes_the_row_and_a_dead_clock_costs_nothing(tmp_path, monkeypatch):
    from scripts.episode import takes_r2v
    monkeypatch.setattr(tp, "ring", lambda: ENTRIES)
    takes_r2v.phases_of(tmp_path / "T01.mp4", {"index": 1}, RECORD)
    assert (tmp_path / "phases.jsonl").exists()
    monkeypatch.setattr(tp, "record", lambda *a: 1 / 0)
    takes_r2v.phases_of(tmp_path / "T02.mp4", {"index": 2}, RECORD)


def test_a_bench_render_reads_the_same_clock(monkeypatch):
    from scripts.bench import h3_arms
    monkeypatch.setattr(tp, "ring", lambda: ENTRIES)
    assert h3_arms.phases_now(RECORD)["s_per_it"] == 10.4
