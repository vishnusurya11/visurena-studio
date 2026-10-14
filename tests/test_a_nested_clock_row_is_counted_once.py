"""The master's upscale is its own row on the episode clock, and is counted once.

OWNER 2026-10-14: RTX VSR 4x replaces the Lanczos 2x in assemble, and its time
must be "its own step so the 6 h clock sees it".  It runs INSIDE assemble, whose
row the runner stamps around the whole script, so a plain second row would be
summed twice by every reader of timing.jsonl (report, step 12, the Command
Center, the ETA) and each would mark the other CONTENDED.  The inner row says
which stage it ran within; the outer row is stamped net of it."""
import pytest

from studio import episode_clock as ck
from studio import eta, timing_sum


@pytest.fixture
def book(tmp_path, monkeypatch):
    monkeypatch.setattr(ck.episode_home, "home", lambda b, n: tmp_path / f"ep{n:02d}")
    return tmp_path


def test_an_inner_row_names_the_stage_it_ran_within(book):
    row = ck.stamp(book, 1, "upscale", 100.0, 160.0, within="assemble")
    assert row["within"] == "assemble" and row["seconds"] == 60.0


def test_a_row_with_no_parent_carries_no_within(book):
    assert "within" not in ck.stamp(book, 1, "lines", 0.0, 10.0)


def test_the_outer_row_is_stamped_net_of_what_ran_within_it(book, monkeypatch):
    clock = iter([1000.0, 1300.0])
    monkeypatch.setattr(ck.time, "time", lambda: next(clock))
    with ck.timed(book, 1, "assemble"):
        ck.stamp(book, 1, "upscale", 1100.0, 1220.0, within="assemble")
    outer = ck.rows(book, 1)[-1]
    assert outer["stage"] == "assemble" and outer["seconds"] == 180.0
    assert outer["net_of_s"] == 120.0


def test_the_total_counts_the_upscale_once(book, monkeypatch):
    clock = iter([1000.0, 1300.0])
    monkeypatch.setattr(ck.time, "time", lambda: next(clock))
    with ck.timed(book, 1, "assemble"):
        ck.stamp(book, 1, "upscale", 1100.0, 1220.0, within="assemble")
    assert sum(r["seconds"] for r in ck.rows(book, 1)) == 300.0


def test_an_older_row_of_the_same_name_is_not_netted(book, monkeypatch):
    ck.stamp(book, 1, "upscale", 10.0, 70.0, within="assemble")     # an earlier run
    clock = iter([1000.0, 1300.0])
    monkeypatch.setattr(ck.time, "time", lambda: next(clock))
    with ck.timed(book, 1, "assemble"):
        pass
    assert ck.rows(book, 1)[-1]["seconds"] == 300.0


def test_a_row_and_its_parent_do_not_contend():
    outer = {"stage": "assemble", "started": "2026-10-14T10:00:00", "ended": "2026-10-14T10:05:00", "seconds": 180}
    inner = {"stage": "upscale", "within": "assemble", "started": "2026-10-14T10:01:00",
             "ended": "2026-10-14T10:03:00", "seconds": 120}
    assert not ck.contended(outer, [outer, inner])
    assert not ck.contended(inner, [outer, inner])


def test_an_unrelated_overlap_still_contends():
    a = {"stage": "assemble", "started": "2026-10-14T10:00:00", "ended": "2026-10-14T10:05:00", "seconds": 300}
    b = {"stage": "takes", "started": "2026-10-14T10:01:00", "ended": "2026-10-14T10:03:00", "seconds": 120}
    assert ck.contended(a, [a, b])


def test_the_upscale_folds_into_step_10_on_the_gpu():
    assert timing_sum.STAGES["upscale"] == ("10", True)
    assert eta.SUB_STEP["upscale"] == "10"
