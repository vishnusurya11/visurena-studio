"""Step 03's vision reads get a timing row and a watchdog (package H, retro 2026-10-20).

Jekyll ep01: timing.jsonl rows 28-29 say `places` 0.3 s while run 6's VL reads took 996 s, and
run 3 left about 312 s untimed.  A read waited up to 600 s (comfy.run_text).  Now each read has
READ_S; a stalled read frees the engine and is asked once more; a second stall leaves the
writer's cells standing, as an unreadable picture always has ("this step never parks").
"""
from __future__ import annotations

import time
from pathlib import Path
from types import SimpleNamespace

import scripts.episode.step_03_places as step
from studio import comfy, episode_clock


def ctx_of(tmp_path, logs):
    return SimpleNamespace(home=tmp_path, book_dir=tmp_path, number=1,
                           log=lambda msg, **kw: logs.append(msg))


def one_setup(monkeypatch, events):
    monkeypatch.setattr(step, "FREE", lambda family: events.append(("free", family)))
    monkeypatch.setattr(step, "by_setup", lambda book, doc: {"door": Path("door.png")})


def test_each_read_runs_under_its_own_deadline_inside_the_rows(tmp_path, monkeypatch):
    events, seen = [], []
    one_setup(monkeypatch, events)
    monkeypatch.setattr(step, "READ", lambda path: seen.append(comfy.ROW_DEADLINE) or [{"x": 1}])
    before = time.time()
    step.read_places(ctx_of(tmp_path, []), {})
    budget = seen[0] + comfy.ROW_GRACE_S - before
    assert step.READ_S - 2 <= budget <= step.READ_S + 2
    with comfy.row_deadline(before + 10):
        seen.clear()
        step.read_places(ctx_of(tmp_path, []), {})
        assert seen[0] == before + 10                    # never past the row's own cap


def test_a_stalled_read_frees_the_engine_and_is_asked_once_more(tmp_path, monkeypatch):
    events, logs = [], []
    one_setup(monkeypatch, events)
    answers = iter([comfy.StillRunning("p1", 150.0), [{"x": 1}]])

    def read(path):
        got = next(answers)
        if isinstance(got, Exception):
            raise got
        return got
    monkeypatch.setattr(step, "READ", read)
    assert step.read_places(ctx_of(tmp_path, logs), {}) == {"door": [{"x": 1}]}
    assert events == [("free", "vl"), ("free", "vl")]
    assert any("WATCHDOG" in line and "door" in line for line in logs)


def stalls(path):
    raise comfy.StillRunning("p", 150.0)


def test_two_stalls_leave_the_writers_cells(tmp_path, monkeypatch):
    events, logs = [], []
    one_setup(monkeypatch, events)
    monkeypatch.setattr(step, "READ", stalls)
    assert step.read_places(ctx_of(tmp_path, logs), {}) == {"door": None}      # stalled, not unreadable
    assert len([e for e in events if e == ("free", "vl")]) == 3


def test_a_stalled_setup_leaves_the_marker_unstamped_so_a_resume_reads_again(tmp_path, monkeypatch):
    """Skeptic on 92eacc1: a transient GPU stall was stamped like an unreadable picture, so
    cells_done() held and cells-from-the-picture (owner ruling 2026-09-28) was skipped for good."""
    one_setup(monkeypatch, [])
    monkeypatch.setattr(step, "READ", stalls)
    (tmp_path / "plan.json").write_text("{}", encoding="utf-8", newline="\n")
    logs = []
    step.cells_from_reads(ctx_of(tmp_path, logs))
    mark = step.stamp(tmp_path)
    assert mark["stalled"] == ["door"] and "plan_sha8" not in mark and not step.cells_done(ctx_of(tmp_path, []))
    assert any("door" in line and "stalled" in line for line in logs)


def test_an_unreadable_picture_still_stamps_the_marker(tmp_path, monkeypatch):
    one_setup(monkeypatch, [])
    monkeypatch.setattr(step, "READ", lambda path: [])
    (tmp_path / "plan.json").write_text("{}", encoding="utf-8", newline="\n")
    step.cells_from_reads(ctx_of(tmp_path, []))
    assert step.stamp(tmp_path)["stalled"] == [] and step.cells_done(ctx_of(tmp_path, []))


def test_a_stall_past_the_rows_own_cap_raises(tmp_path, monkeypatch):
    """A row-cap overrun is the cap's to handle, never swallowed as an unreadable picture."""
    events = []
    one_setup(monkeypatch, events)
    monkeypatch.setattr(step, "READ", stalls)
    with comfy.row_deadline(time.time() - 1):
        try:
            step.read_places(ctx_of(tmp_path, []), {})
        except comfy.StillRunning:
            pass
        else:
            raise AssertionError("a spent row's stall was swallowed")
    assert events == [("free", "vl")]                   # the one free before the reads, no retry


def test_the_cells_step_writes_a_timing_row(tmp_path, monkeypatch):
    one_setup(monkeypatch, [])
    monkeypatch.setattr(step, "READ", lambda path: [])
    (tmp_path / "plan.json").write_text("{}", encoding="utf-8", newline="\n")
    step.write_cells(ctx_of(tmp_path, []))
    rows = [r for r in episode_clock.rows(tmp_path, 1) if r["stage"] == "places"]
    assert [r["note"] for r in rows] == ["03_03 cells from the picture"] and rows[0]["ok"]
