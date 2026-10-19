"""Ship review of the leftover-window rule (fix round, 2026-10-19).

A drive killed during steps 10-12 of an owner's repair left its window open after step 09 had already
cleared the owner's receipt (work_orders.clear_taken), so the next drive's start closed it as UNBACKED
and the rest of the repair ran on the episode's spent 6 h.  The repair is owed until step 12 re-delivers:
a window holds while every order it names is an OWNER order whose receipt still stands, or whose step
completed (receipt cleared) and the episode has not been delivered again since the window opened.  A
receipt naming ANOTHER order still closes it (the existing rule).

Minor: a second owner order for the same step is taken by the runner AFTER the drive's start; the open
window now adopts it (`window_for`), so the next drive's start does not close the repair mid-way.
Temp db and files; no GPU, no network."""
from __future__ import annotations

import os

from studio import repair_clock, work_orders
from tests.test_an_owner_repair_runs_on_its_own_clock import delivered, ordered
from tests.test_episode_runner import book, conn  # noqa: F401

OPENED = 1_792_433_901.9
"""ep01's window: the killed run's start, 2026-10-19 18:18:21Z."""


def delivered_at(home, epoch: float) -> None:
    """The manifest step 12 wrote, stamped at `epoch`."""
    delivered(home)
    os.utime(home / "manifest.json", (epoch, epoch))


def step_09_completed(home) -> None:
    work_orders.clear_taken(home, "09")


def test_a_window_whose_step_completed_holds_until_it_redelivers(conn, book, tmp_path):
    delivered_at(tmp_path, OPENED - 40_000)
    window = repair_clock.open_window(tmp_path, {"09": ordered(conn, tmp_path)}, OPENED)
    step_09_completed(tmp_path)
    assert repair_clock.backed(conn, tmp_path, window)
    assert repair_clock.close_unbacked(conn, tmp_path) is None


def test_a_window_whose_repair_redelivered_closes(conn, book, tmp_path):
    delivered_at(tmp_path, OPENED - 40_000)
    window = repair_clock.open_window(tmp_path, {"09": ordered(conn, tmp_path)}, OPENED)
    step_09_completed(tmp_path)
    delivered_at(tmp_path, OPENED + 5_000)                  # step 12 re-delivered, the drive was killed after
    assert not repair_clock.backed(conn, tmp_path, window)
    assert repair_clock.close_unbacked(conn, tmp_path)["closed_by"] == repair_clock.UNBACKED


def test_a_completed_cure_backs_nothing(conn, book, tmp_path):
    delivered_at(tmp_path, OPENED - 40_000)
    window = repair_clock.open_window(tmp_path, {"09": ordered(conn, tmp_path, by="autopilot")}, OPENED)
    step_09_completed(tmp_path)
    assert not repair_clock.backed(conn, tmp_path, window)


def test_the_open_window_adopts_a_newer_owner_order_for_its_step(conn, book, tmp_path):
    delivered_at(tmp_path, OPENED - 40_000)
    first = ordered(conn, tmp_path)
    window = repair_clock.open_window(tmp_path, {"09": first}, OPENED)
    second = ordered(conn, tmp_path)                        # the runner took a second order after the start
    got = repair_clock.window_for(conn, tmp_path, OPENED + 600)
    assert got["orders"] == {"09": second} and got["opened_at"] == window["opened_at"]
    assert repair_clock.read(tmp_path)["orders"] == {"09": second}
    assert repair_clock.backed(conn, tmp_path, got)


def test_an_autopilot_order_is_never_adopted(conn, book, tmp_path):
    delivered_at(tmp_path, OPENED - 40_000)
    first = ordered(conn, tmp_path)
    repair_clock.open_window(tmp_path, {"09": first}, OPENED)
    ordered(conn, tmp_path, by="autopilot")
    assert repair_clock.window_for(conn, tmp_path, OPENED + 600)["orders"] == {"09": first}


def test_owner_ids_names_only_the_owners_orders(conn, book, tmp_path):
    mine, cure = ordered(conn, tmp_path), ordered(conn, tmp_path, by="autopilot")
    assert work_orders.owner_ids(conn, [mine, cure, 99_999]) == {mine}
    assert work_orders.owner_ids(conn, []) == set()
