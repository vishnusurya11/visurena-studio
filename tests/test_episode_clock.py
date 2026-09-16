"""An episode's wall time, stage by stage: the number nine episodes never had."""
import json
import time

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
