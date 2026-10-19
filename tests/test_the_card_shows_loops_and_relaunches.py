"""The live card shows the loops as they happen (timeline debate 2026-10-18, D1; owner go): the
runner never steps back inside a run, so a loop is (a) a later step re-running an earlier step's
work inside its own wall -- 08 redraws 07's grids, 11 re-runs 09's takes -- billed by timing.jsonl's
work names, and (b) a relaunch that enters an earlier step.  No arrows: a mark names who did the work."""
from __future__ import annotations

from studio.command_center import loops

ROWS = [
    {"stage": "step_07", "started": "2026-10-18T10:00:00", "seconds": 0, "event": "started"},
    {"stage": "grids", "started": "2026-10-18T10:00:05", "seconds": 300.0},
    {"stage": "step_08", "started": "2026-10-18T10:10:00", "seconds": 0, "event": "started"},
    {"stage": "panels", "started": "2026-10-18T10:10:05", "seconds": 60.0},
    {"stage": "grids", "started": "2026-10-18T10:20:00", "seconds": 500.0},
    {"stage": "grids", "started": "2026-10-18T10:30:00", "seconds": 520.0},
    {"stage": "step_11", "started": "2026-10-18T12:00:00", "seconds": 0, "event": "started"},
    {"stage": "take_dq", "started": "2026-10-18T12:10:00", "seconds": 90.0},
]


def test_work_an_earlier_step_owns_is_billed_to_it_inside_the_later_step():
    got = loops.borrowed(ROWS)
    assert {(b["host"], b["owner"], b["sub"], b["n"], b["secs"]) for b in got} == {
        ("08", "07", "grids", 2, 1020.0), ("11", "09", "take_dq", 1, 90.0)}


def test_a_steps_own_work_is_not_a_loop():
    assert all(not (b["host"] == "07" and b["owner"] == "07") for b in loops.borrowed(ROWS))


def test_rows_before_this_make_are_left_out():
    from studio import eta
    since = eta.to_epoch("2026-10-18T11:00:00")
    assert [(b["host"], b["owner"]) for b in loops.borrowed(ROWS, since)] == [("11", "09")]


def test_a_loop_reads_who_ran_whose_work():
    b = {"host": "08", "owner": "07", "sub": "grids", "n": 2, "secs": 1020.0}
    assert loops.loop_words(b) == "08 re-ran 07's grids ×2 · 17m"


EVENTS = [
    {"run_id": "r1", "step_id": "01", "event": "started", "event_ts": "2026-10-18T15:00:00Z"},
    {"run_id": "r1", "step_id": "11", "event": "started", "event_ts": "2026-10-18T17:00:00Z"},
    {"run_id": "r1", "step_id": "11", "event": "failed", "event_ts": "2026-10-18T17:12:00Z"},
    {"run_id": "r2", "step_id": "06", "event": "started", "event_ts": "2026-10-18T17:20:00Z"},
    {"run_id": "r2", "step_id": "06", "event": "completed", "event_ts": "2026-10-18T17:21:00Z"},
    {"run_id": "r2", "step_id": "07", "event": "started", "event_ts": "2026-10-18T17:21:00Z"},
]


def test_each_run_says_where_it_entered_and_how_it_ended():
    got = loops.attempts(EVENTS)
    assert [(a["run"], a["entered"], a["last"], a["how"]) for a in got] == [
        ("r1", "01", "11", "failed"), ("r2", "06", "07", "started")]


def test_only_this_makes_runs():
    assert [a["run"] for a in loops.attempts(EVENTS, runs={"r2"})] == ["r2"]


def test_the_loops_line_joins_the_relaunch_and_the_borrowed_work():
    text = loops.loops_text(loops.attempts(EVENTS), loops.borrowed(ROWS))
    assert text.startswith("run 2 of 2 · entered at 06") and "08 re-ran 07's grids ×2" in text
    assert loops.loops_text([], []) == ""


def test_the_card_and_its_template_carry_the_loops_line():
    from pathlib import Path
    from studio.command_center import models
    assert "loops_text" in models.Progress.model_fields
    live = (Path(loops.__file__).parent / "templates" / "_unit_live.html").read_text(encoding="utf-8")
    js = (Path(loops.__file__).parent / "static" / "progress.js").read_text(encoding="utf-8")
    assert 'data-k="loops"' in live and "text('loops'" in js


def test_a_run_that_ended_on_a_finished_step_stopped_after_it():
    # live Jekyll ep01 2026-10-18: run 9's last row was 08 completed, then a restart; not a success
    runs = [{"run": "r9", "entered": "06", "last": "08", "how": "completed", "at": None},
            {"run": "r10", "entered": "01", "last": "09", "how": "started", "at": None}]
    assert loops.attempts_words(runs) == "run 2 of 2 · entered at 01 after run 1 stopped after 08"


def test_the_strip_names_the_relaunch_and_its_cause():
    words = loops.attempts_words(loops.attempts(EVENTS))
    assert words.startswith("run 2 of 2 · entered at 06 after run 1 failed at 11")
