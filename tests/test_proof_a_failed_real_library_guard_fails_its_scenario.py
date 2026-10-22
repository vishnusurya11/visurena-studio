"""A scenario whose real-library stat guard failed never reads PASS (2026-10-21 window: F5's guard
row said `REAL LIBRARY TOUCHED: library\\.device\\decisions.jsonl` and its summary row still said
passed, because summary_row tallied only the per-point rows).  And a run names the code it ran on:
HEAD and the tracked files' state at its start and its end, so a run that another session's commit
moved under it says so."""
from __future__ import annotations

from scripts.proof import rehearse

SC = rehearse.TABLE["F5"]
POINT = [{"id": "F5", "passed": True, "trace": "abc"}]


def guard(passed: bool, state: str = "n/a") -> dict:
    return {"check": "A-real", "passed": passed, "instrument": "guard", "instrument_state": state,
            "detail": "" if passed else "REAL LIBRARY TOUCHED: x"}


def test_a_failed_guard_fails_the_summary_row():
    r = rehearse.summary_row(SC, POINT, 1, None, guard=guard(False))
    assert r["passed"] is False and "A-real guard failed" in r["detail"]


def test_a_clean_guard_leaves_the_summary_row_passing():
    assert rehearse.summary_row(SC, POINT, 1, None, guard=guard(True))["passed"] is True


def test_a_guard_whose_instrument_failed_counts_neither_way():
    assert rehearse.summary_row(SC, POINT, 1, None, guard=guard(False, "failed"))["passed"] is True


def fake_git(head: str, dirty: str):
    return lambda *args: head if args[0] == "rev-parse" else dirty


def test_the_code_state_is_head_and_the_tracked_files_changed():
    state = rehearse.code_state(fake_git("abc123\n", " M studio/x.py\n"))
    assert state == {"head": "abc123", "dirty": [" M studio/x.py"]}


def test_a_run_the_code_moved_under_says_so():
    start, end = {"head": "aaaaaaaa1", "dirty": []}, {"head": "bbbbbbbb2", "dirty": [" M studio/x.py"]}
    note = rehearse.code_note(start, end)
    assert "code moved during the run" in note and "aaaaaaaa" in note and "bbbbbbbb" in note
    assert rehearse.code_note(start, dict(start)) == ""
