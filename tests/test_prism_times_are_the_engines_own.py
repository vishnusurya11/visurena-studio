"""A Prism image's time is ComfyUI's own (execution_start -> execution_success), not the client's
wall clock: the client polls every 5 s, so every model read 10.1-10.2 s on the first run."""
from __future__ import annotations

from prism.board import warm_median
from prism.timing import backfill, exec_seconds, job_key


def record(style="anime_a", subject="count", model="krea2", start=1000, end=8260):
    return {"status": {"messages": [["execution_start", {"timestamp": start}],
                                    ["execution_cached", {"timestamp": start + 5}],
                                    ["execution_success", {"timestamp": end}]]},
            "outputs": {"9": {"images": [{"filename": f"{subject}__{model}_00001_.png",
                                          "subfolder": f"prism\\{style}"}]}}}


def test_the_time_is_start_to_success():
    assert exec_seconds(record()) == 7.3


def test_a_record_without_success_has_no_time():
    failed = record()
    failed["status"]["messages"].pop()
    assert exec_seconds(failed) is None


def test_the_job_is_read_from_the_saved_names():
    assert job_key(record("anime_b", "chase", "qwen_image_2_1")) == ("anime_b", "chase", "qwen_image_2_1")
    assert job_key({"outputs": {"9": {"images": [{"filename": "x_00001_.png", "subfolder": "other"}]}}}) is None


def test_backfill_puts_the_latest_engine_time_on_its_row():
    rows = [{"style": "anime_a", "subject": "count", "model": "krea2", "seconds": 10.2, "cold": False}]
    history = {"p1": record(start=1000, end=4000), "p2": record(start=9000, end=16000)}
    assert backfill(rows, history)[0]["exec_seconds"] == 7.0


def test_the_median_reads_the_engine_time_when_it_has_one():
    rows = [{"style": "s", "model": "m", "seconds": 10.2, "exec_seconds": 6.0, "cold": False},
            {"style": "s", "model": "m", "seconds": 10.2, "exec_seconds": 8.0, "cold": False}]
    assert warm_median(rows, "s", "m") == 7.0
