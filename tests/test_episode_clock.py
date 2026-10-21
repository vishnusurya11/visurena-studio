"""An episode's wall time, stage by stage: the number nine episodes never had."""
import json
import time
from pathlib import Path

import pytest

from studio import episode_clock as ck


@pytest.fixture
def book(tmp_path, monkeypatch):
    monkeypatch.setattr(ck.episode_home, "home", lambda b, n: tmp_path / f"ep{n:02d}")
    return tmp_path


def test_a_stage_is_stamped_with_its_seconds(book):
    row = ck.stamp(book, 10, "lines", 1000.0, 1075.5)
    assert row["seconds"] == 75.5 and row["ok"] is True
    assert ck.rows(book, 10) == [row]


def test_a_retry_is_another_row_not_an_overwrite(book):
    ck.stamp(book, 10, "takes", 0, 100)
    ck.stamp(book, 10, "takes", 200, 260)
    assert [r["seconds"] for r in ck.rows(book, 10)] == [100, 60]


def test_timed_records_a_failure_and_still_raises(book):
    with pytest.raises(RuntimeError):
        with ck.timed(book, 10, "sheets"):
            raise RuntimeError("the drawer said no")
    assert ck.rows(book, 10)[0]["ok"] is False


def test_a_stage_past_twice_its_norm_is_slow():
    assert ck.slow({"stage": "respot", "seconds": 61})
    assert not ck.slow({"stage": "respot", "seconds": 59})
    assert not ck.slow({"stage": "plan", "seconds": 99999}), "authoring has no norm"


def test_the_report_totals_and_names_the_slow_stage(book):
    ck.stamp(book, 10, "lines", 0, 300)
    ck.stamp(book, 10, "respot", 300, 400)        # 100 s against a 30 s norm
    said = ck.report(book, 10)
    assert "TOTAL" in said and "400" in said
    assert "respot" in said and "SLOW" in said
    assert "lines" in said


def test_no_rows_is_said_not_zeroed(book):
    assert ck.report(book, 10) == "no stages timed"


# ---- A25 (face debate 2026-10-21): a span is not a cost; the stage's price is wall minus GPU ----

OVERLAP = Path(__file__).parent / "fixtures" / "ep01_face_refine" / "stage_2026-10-19_1338.json"


def test_a_stage_carries_the_extras_its_run_measured(book):
    with ck.timed(book, 10, "face_refine") as extra:
        extra["gpu_busy_s"] = 898.0
    row = ck.rows(book, 10)[0]
    assert row["gpu_busy_s"] == 898.0 and row["wall_s"] == row["seconds"]


def test_the_cpu_part_is_wall_minus_gpu_never_a_sum_of_spans():
    """ep01's 12 refined takes each logged a `seconds` of 32-655 s under up to 9 concurrent lanes:
    5.4x the stage's 972 s wall.  A span overlaps; only wall - GPU-busy is CPU exposure (74 s)."""
    fx = json.loads(OVERLAP.read_text(encoding="utf-8"))
    spans = list(fx["take_spans_s"].values())
    assert sum(spans) > 5 * fx["wall_s"] and fx["gpu_busy_s"] <= fx["wall_s"]
    assert ck.cpu_s({"seconds": fx["wall_s"], "gpu_busy_s": fx["gpu_busy_s"]}) == 74.0
    assert ck.cpu_s({"seconds": fx["wall_s"]}) is None
    assert ck.cpu_s({"seconds": 10.0, "gpu_busy_s": 12.0}) == 0.0
