"""studio/command_center/vitals.py (progress tracker spec §7): is the run
alive?  Pure functions; the process table comes through an injectable lookup,
so no test depends on the machine it runs on."""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import pytest

from studio import progress
from studio.command_center import legacy_progress as lp
from studio.command_center import procs, vitals

FIX = Path(__file__).resolve().parent / "fixtures" / "progress"
RUN_T0 = 1_000_000.0


def _p(pid=7, started=RUN_T0 - 30, cmd="python scripts/episode/drive.py 20260827135508_the-war-of-the-worlds 17"):
    return procs.ProcInfo(pid, started, cmd)


# --- finding the drive ---


def test_the_drive_is_found_by_codex_and_episode_number():
    table = [_p(1, cmd="python command_center.py --port 8700"),
             _p(2, cmd="python scripts/episode/drive.py 20260827135508_the-war-of-the-worlds 16"),
             _p(3, started=RUN_T0 - 10), _p(4, started=RUN_T0 - 20)]
    assert procs.find_drive(table, "20260827135508", 17).pid == 4   # the earliest of the chain
    assert procs.find_drive(table, "20260827135508", 18) is None


def test_an_episode_number_is_a_whole_token():
    table = [_p(1, cmd="python scripts/episode/drive.py 20260827135508_x 170")]
    assert procs.find_drive(table, "20260827135508", 17) is None


@pytest.mark.skipif(sys.platform != "win32", reason="the process table is read through the Windows API")
def test_this_process_is_in_the_table_with_its_command_line():
    me = [p for p in procs.list_processes() if p.pid == os.getpid()]
    assert me and "pytest" in me[0].cmdline and abs(me[0].started - time.time()) < 86400


# --- liveness ---


def test_no_drive_process_is_dead():
    assert vitals.pid_alive(None, RUN_T0) is False


def test_a_drive_started_after_the_run_began_is_another_process():
    assert vitals.pid_alive(_p(started=RUN_T0 + 600), RUN_T0) is False
    assert vitals.pid_alive(_p(started=RUN_T0 - 1), RUN_T0) is True


def test_budget_for_a_192_frame_take_is_580_s():
    assert vitals.step_budget("09", frames=192, first=False, history={}) == pytest.approx(580.8)
    assert vitals.step_budget("09", frames=192, first=True, history={}) == pytest.approx(880.8)


def test_budget_for_the_plan_is_ten_minutes_and_else_twice_the_norm():
    assert vitals.step_budget("02", history={"02": [5000.0] * 9}) == 600.0
    assert vitals.step_budget("11", history={"11": [100.0, 200.0, 300.0]}) == 600.0 * 1   # floor
    assert vitals.step_budget("11", history={"11": [1000.0] * 5}) == 2000.0


def _ep17_state() -> dict:
    rows = [{"event_ts": "2026-10-05T00:43:47.81Z", "step_id": "02", "event": "started",
             "run_id": "20260827135508__episode__20261005004347"}]
    return progress.fold(lp.db_step_events(rows, rows[0]["run_id"], {"02": "plan"}))


def test_the_ep17_replay_with_the_drive_gone_is_dead():
    v = vitals.vital(_ep17_state(), alive=False, quiet_s=30.0, budget_s=600.0)
    assert v["vital"] == "dead"


def test_a_reused_pid_is_dead():
    state = _ep17_state()
    alive = vitals.pid_alive(_p(started=state["t0"] + 3600), state["t0"])
    assert vitals.vital(state, alive=alive, quiet_s=5.0, budget_s=600.0)["vital"] == "dead"


def test_the_ep16_replay_mid_shoot_is_live():
    rows = json.loads((FIX / "ep16_shots.json").read_text(encoding="utf-8"))
    evs = [{"t": 0.0, "ev": "step", "step": "09", "state": "start"},
           {"t": 1.0, "ev": "plan", "items": [[f"T{r['index']:02d}", r["frames"]] for r in rows], "kept": []},
           {"t": 150.0, "ev": "item", "item": "T00", "weight": 175, "secs": 150.9, "state": "done"}]
    v = vitals.vital(progress.fold(evs), alive=True, quiet_s=20.0, budget_s=580.0)
    assert v["vital"] == "live"


def test_quiet_then_stalled_by_the_budget():
    state = _ep17_state()
    assert vitals.vital(state, alive=True, quiet_s=90.0, budget_s=600.0)["vital"] == "quiet"
    stalled = vitals.vital(state, alive=True, quiet_s=1320.0, budget_s=600.0)
    assert stalled["vital"] == "stalled" and stalled["reason"] == "quiet 22m · budget 10m"


def test_an_end_outranks_the_process():
    state = {**_ep17_state(), "outcome": "completed"}
    assert vitals.vital(state, alive=False, quiet_s=9e9, budget_s=1.0)["vital"] == "done"
    for outcome in ("refused", "deferred"):
        got = vitals.vital({**state, "outcome": outcome}, alive=False, quiet_s=0, budget_s=1, reason="G-LIGHT")
        assert got["vital"] == outcome and got["reason"] == "G-LIGHT"


def test_a_crashed_run_is_dead():
    assert vitals.vital({**_ep17_state(), "outcome": "failed"}, alive=True, quiet_s=0, budget_s=1)["vital"] == "dead"


def test_quiet_seconds_from_the_newest_runner_signal():
    assert vitals.quiet_seconds([10.0, 50.0, 30.0], now=80.0) == 30.0
    assert vitals.quiet_seconds([], now=80.0) is None


def test_a_plan_json_touched_by_an_outsider_is_not_a_signal(tmp_path):
    home = tmp_path / "ep17"
    home.mkdir()
    (home / "drive_run01.log").write_text((FIX / "ep17_drive_run01.log").read_text(encoding="utf-8"), encoding="utf-8")
    os.utime(home / "drive_run01.log", (RUN_T0, RUN_T0))
    before = lp.derive(home, [], [])["signals"]
    (home / "plan.json").write_text("{}", encoding="utf-8")
    assert lp.derive(home, [], [])["signals"] == before == [RUN_T0]


def test_the_trace_keeps_the_last_thirty_minutes():
    assert vitals.trace([10.0, 1000.0, 2000.0, 2500.0], now=2600.0) == [1000.0, 2000.0, 2500.0]
