"""episode_clock.stamp never writes a negative row (P12; ep01 timing.jsonl held -421.1 s)."""
import json

from studio import episode_clock


def _rows(tmp_path):
    return [json.loads(l) for l in (tmp_path / "episodes" / "ep01" / "timing.jsonl").read_text().splitlines()]


def test_the_ep01_negative_row_stamps_to_zero_with_its_overlap(tmp_path, monkeypatch):
    monkeypatch.setattr(episode_clock, "path", lambda book, n: tmp_path / "episodes" / "ep01" / "timing.jsonl")
    row = episode_clock.stamp(tmp_path, 1, "step_10", 1000.0, 1900.0, net_of=1321.1)
    assert row["seconds"] == 0.0
    assert row["gross_s"] == 900.0 and row["overlap_s"] == 421.1 and row["net_of_s"] == 1321.1


def test_a_normal_nested_row_is_net_of_its_inner(tmp_path, monkeypatch):
    monkeypatch.setattr(episode_clock, "path", lambda book, n: tmp_path / "episodes" / "ep01" / "timing.jsonl")
    row = episode_clock.stamp(tmp_path, 1, "assemble", 1000.0, 1600.0, net_of=200.0)
    assert (row["seconds"], row["gross_s"], row["overlap_s"]) == (400.0, 600.0, 0.0)


def test_every_row_has_epoch_t0_t1_and_takes_a_device(tmp_path, monkeypatch):
    monkeypatch.setattr(episode_clock, "path", lambda book, n: tmp_path / "episodes" / "ep01" / "timing.jsonl")
    episode_clock.stamp(tmp_path, 1, "qc", 5.0, 65.0, device="gpu")
    row = _rows(tmp_path)[0]
    assert (row["t0"], row["t1"], row["device"]) == (5.0, 65.0, "gpu")
    assert "overlap_s" not in row and "gross_s" not in row     # a plain row stays as it was


def test_ep01_replay_no_row_of_the_stamped_timing_is_negative(tmp_path, monkeypatch):
    """R8: the ep01 -421.1 s row, re-stamped from its own fields, is 0 with its overlap."""
    from datetime import datetime
    from pathlib import Path
    monkeypatch.setattr(episode_clock, "path", lambda book, n: tmp_path / "episodes" / "ep01" / "timing.jsonl")
    fix = Path(__file__).parent / "fixtures" / "ep01_replay" / "P12" / "timing.jsonl"
    old = [json.loads(l) for l in fix.read_text(encoding="utf-8").splitlines() if l.strip()]
    for r in old:
        episode_clock.stamp(tmp_path, 1, r["stage"], datetime.fromisoformat(r["started"]).timestamp(),
                            datetime.fromisoformat(r["ended"]).timestamp(), r["ok"], r.get("note", ""),
                            r.get("within", ""), net_of=float(r.get("net_of_s") or 0.0))
    new = _rows(tmp_path)
    assert len(old) == 137 and min(r["seconds"] for r in old) < 0
    assert all(r["seconds"] >= 0 for r in new)
    worst = next(r for r in new if r.get("net_of_s") == 1993.8)
    assert worst["seconds"] == 0.0 and 420 <= worst["overlap_s"] <= 423
