"""Ship review of the repair clock, minor 1: `repair_clock.window_for` reused ANY repair.json.  A drive
killed before its end (ep01, 2026-10-19 11:18 PDT: the main session killed the drive that queued all 28
takes) leaves its window open, and the next launch -- an owner's repair or not -- ran on it.

Now a drive's start closes a leftover window that no owner receipt backs (every order the window names is
an OWNER redo still receipted beside the episode, K12).  A backed window is the same owed order: it holds,
so the repair's clock keeps what the killed run spent.  A relaunch INSIDE a drive is untouched (window_for
still continues the open window after the receipt clears).  Temp db and files; no GPU, no network."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from studio import repair_clock, work_orders
from tests.test_an_owner_repair_runs_on_its_own_clock import delivered, ordered
from tests.test_episode_runner import CODEX, book, conn  # noqa: F401

FIX = Path(__file__).parent / "fixtures" / "ep01_replay" / "repair_rerun"


def left_open(home, orders: dict) -> dict:
    """A window a killed drive left behind, opened at the killed run's start."""
    return repair_clock.open_window(home, orders, 1_792_433_901.9)


def test_ep01s_leftover_window_is_the_one_the_killed_run_opened():
    window = json.loads((FIX / "repair.json").read_text(encoding="utf-8"))
    assert window["steps"] == ["09"] and window["orders"] == {"09": 38} and window["cap_s"] == 8_580.0


def test_a_window_no_receipt_backs_is_closed_at_drive_start(conn, book, tmp_path):
    delivered(tmp_path)
    left_open(tmp_path, {"09": 38})
    closed = repair_clock.close_unbacked(conn, tmp_path)
    assert closed["orders"] == {"09": 38} and "no owner receipt" in closed["closed_by"]
    assert repair_clock.read(tmp_path) is None and repair_clock.history(tmp_path)[-1] == closed


def test_a_window_its_owner_receipt_backs_holds(conn, book, tmp_path):
    delivered(tmp_path)
    order_id = ordered(conn, tmp_path)
    window = left_open(tmp_path, {"09": order_id})
    assert repair_clock.close_unbacked(conn, tmp_path) is None
    assert repair_clock.read(tmp_path) == window


def test_an_autopilot_cure_backs_no_window(conn, book, tmp_path):
    delivered(tmp_path)
    order_id = ordered(conn, tmp_path, by="autopilot")
    left_open(tmp_path, {"09": order_id})
    assert repair_clock.close_unbacked(conn, tmp_path) is not None


def test_a_receipt_for_another_order_backs_no_window(conn, book, tmp_path):
    delivered(tmp_path)
    first = ordered(conn, tmp_path)
    left_open(tmp_path, {"09": first})
    ordered(conn, tmp_path)                       # a newer owner order replaced the receipt
    assert repair_clock.close_unbacked(conn, tmp_path) is not None
    assert repair_clock.window_for(conn, tmp_path, 2_000.0)["opened_at"] == 2_000.0


def test_no_window_closes_nothing(conn, book, tmp_path):
    assert repair_clock.close_unbacked(conn, tmp_path) is None
    assert repair_clock.history(tmp_path) == []


def test_the_drive_start_closes_the_leftover_and_says_so(conn, book, tmp_path):
    from scripts.episode import drive
    delivered(tmp_path)
    shutil.copy(FIX / "repair.json", tmp_path / repair_clock.WINDOW)
    said = []
    drive.leftover_window(tmp_path, conn, said.append)
    assert repair_clock.read(tmp_path) is None
    assert said and "closed a leftover repair window" in said[0]


def test_the_drive_start_keeps_a_backed_window_quietly(conn, book, tmp_path):
    from scripts.episode import drive
    delivered(tmp_path)
    left_open(tmp_path, {"09": ordered(conn, tmp_path)})
    said = []
    drive.leftover_window(tmp_path, conn, said.append)
    assert repair_clock.read(tmp_path) is not None and said == []
    assert work_orders.owner_receipts(conn, tmp_path)
