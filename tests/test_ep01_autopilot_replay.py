"""R9 (Jekyll Kawajiri ep01 retro, P13): replay the real ep01 drive.jsonl through
derive().  Every failing end whose code was already replaced by a later commit, or
that met a dirty tree, must be answered by a relaunch or a wait -- never the brain,
never a park.  The fixture is a copy of episodes/ep01/drive.jsonl; $0, no clock."""
from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from studio import autopilot as ap
from studio.autopilot import Signals, State

FIXTURE = Path(__file__).parent / "fixtures" / "ep01_replay" / "P13" / "drive.jsonl"
REFUSED = "ep01: REFUSED: something no table row knows"        # the brain's fallback shape
HEAD = "f" * 40


def ledger() -> list[dict]:
    return [json.loads(line) for line in FIXTURE.read_text(encoding="utf-8").splitlines() if line.strip()]


def failing_ends(rows: list[dict]) -> list[int]:
    """Indices of `end` rows that stopped a run on a non-zero, non-boundary code."""
    return [i for i, r in enumerate(rows) if r.get("event") == "end" and r.get("code") == 1]


def signals_at(rows: list[dict], upto: int, **kw) -> Signals:
    base = Signals(drive_rows=rows[:upto + 1], exit_code=None, lock=None, proc_alive=False, uploads_rows=[],
                   parked_rows=[], home_files={"plan.json"}, log_tail=REFUSED, porcelain="", engine_up=True,
                   clock_spent_s=0.0, brain_attempts=0, brain_verdict=None, paused=False, head_sha=HEAD,
                   media_spent_usd=0.0, failed_sha=ap.failed_sha(rows[:upto + 1]))
    return replace(base, **kw)


def test_the_fixture_is_ep01s_ledger():
    rows = ledger()
    assert len(failing_ends(rows)) >= 6 and rows[0]["event"] == "start"


def test_every_failure_at_an_older_head_is_a_relaunch_never_a_brain_or_a_park():
    rows = ledger()
    for i in failing_ends(rows):
        got = ap.derive(signals_at(rows, i), 1)
        assert got.state is State.IDLE and got.reason == "head_moved", (i, got.state, got.reason)


def test_every_failure_met_by_a_dirty_tree_waits_never_asks_or_parks():
    rows = ledger()
    for i in failing_ends(rows):
        got = ap.derive(signals_at(rows, i, head_sha=rows[i]["sha"], porcelain=" M studio/judged_gate.py\n"), 1)
        assert got.state is State.WAIT_TREE, (i, got.state)


def test_the_same_failures_at_their_own_head_on_a_clean_tree_keep_todays_path():
    rows = ledger()
    for i in failing_ends(rows):
        got = ap.derive(signals_at(rows, i, head_sha=rows[i]["sha"]), 1)
        assert got.state is State.NEEDS_BRAIN, (i, got.state)


def test_the_replay_counts_zero_false_asks_or_parks():
    rows, asks = ledger(), 0
    for i in failing_ends(rows):
        for kw in ({}, {"porcelain": " M studio/x.py\n", "head_sha": rows[i]["sha"]}):
            asks += ap.derive(signals_at(rows, i, **kw), 1).state in (State.NEEDS_BRAIN, State.PARKED)
    assert asks == 0
