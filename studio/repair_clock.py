"""The repair clock (owner ruling 2026-10-19, "Own repair clock").

An owner-ordered repair of a DELIVERED episode runs on its own capped clock, charged and logged
apart; the 6 h rule (run_budget.OWNER_LIMIT_SECONDS) stays intact for every normal run.  Jekyll
HEL ep01 had spent 21,673 s when the owner ordered its face repair, so each launch charged the
budget with that and cut the refine and the tiny-face rung before they could run
(docs/audit/2026-10-19_face_blur/RERUN.md section 0).

    repair.json    the open window: opened_at (epoch), cap_s, steps, orders {step: order id}
    repair.jsonl   one row per closed window: the same, plus closed_at and spent_s

A window opens when the runner has taken the owner's orders and an OWNER redo receipt (K12,
work_orders.owner_receipts; an autopilot cure is not one) names a step of an episode whose
manifest.json exists.  It lasts until its drive ends (drive.py closes it), so a relaunch inside
the drive continues it.  Its budget is charged with the repair-tagged run spans since it opened
(run_clock.repair_spent), never with the episode's earlier hours, and its limit is the cap.

THE CAP (never unlimited): the clock's own price for the work the order makes owed -- the share of
the earliest redone step and of every step after it, each priced as its first -- plus the judges'
pool, because a repair re-signs its eyes.  A redo of 09: (105+6+20+3+3)/300 x 18,000 + 360 =
8,580 s (2.38 h), against ep01's expected 2,236 s refine + 984 s rung + 30-40 min cut/QC.  It binds
as the owner's limit binds a normal run: every rung and costly check is priced against it
(Budget.leaves_reserve, checks_cut); owed firsts still run.  A `CAP repair` line says when it is spent.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

from studio import run_clock, work_orders
from studio.run_budget import EPISODE_CEILING_SECONDS, EPISODE_SHARES, OWNER_LIMIT_SECONDS, Budget

WINDOW = "repair.json"
LOG = "repair.jsonl"
MARGIN = "judges"
"""The margin's share: the judges' pool, which the firsts' shares do not hold."""


def cap_for(steps, shares: dict = EPISODE_SHARES, ceiling: float = EPISODE_CEILING_SECONDS) -> float:
    """The priced firsts of the earliest redone step and every step after it, plus the judges' pool;
    never past the owner's limit."""
    first = min(steps)
    owed = sum(v for s, v in shares.items() if s.isdigit() and s >= first)
    return min((owed + shares.get(MARGIN, 0.0)) * ceiling, OWNER_LIMIT_SECONDS)


def delivered(home) -> bool:
    """Step 12 delivered the episode once: its manifest is on disk."""
    return (Path(home) / "manifest.json").exists()


def read(home) -> dict | None:
    """The open window, or None."""
    path = Path(home) / WINDOW
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
    except (ValueError, OSError):
        return None


def open_window(home, orders: dict, started: float | None = None) -> dict:
    """Write the window for these receipted orders, opened at `started` (the run's start) or now."""
    window = {"opened_at": float(started if started is not None else time.time()),
              "cap_s": cap_for(list(orders)), "steps": sorted(orders),
              "orders": {k: int(v) for k, v in sorted(orders.items())}}
    path = Path(home) / WINDOW
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(window), encoding="utf-8")
    os.replace(tmp, path)
    return window


def window_for(conn, home, started: float | None) -> dict | None:
    """The window this drive runs in: the open one, else one opened now for an owner redo of a
    delivered episode, else None (a normal run, on the episode's 6 h)."""
    if (window := read(home)) is not None:
        return window
    orders = work_orders.owner_receipts(conn, home)
    if not orders or not delivered(home):
        return None
    return open_window(home, orders, started)


def spent(home, window: dict) -> float:
    return run_clock.repair_spent(home, since=float(window["opened_at"]))


def budget(home, window: dict, clock=time.monotonic) -> Budget:
    """The repair's budget: the episode's shares under its ceiling, limited by the cap, charged
    with what the window already spent."""
    b = Budget(EPISODE_CEILING_SECONDS, EPISODE_SHARES, clock=clock, limit=float(window["cap_s"]))
    b.charge(spent(home, window))
    return b


def capped(home, window: dict) -> bool:
    return spent(home, window) >= float(window["cap_s"])


def open_line(home, window: dict, episode_s: float) -> str:
    return (f"REPAIR CLOCK: an owner redo of step(s) {', '.join(window['steps'])} on a delivered episode runs on "
            f"its own clock: {spent(home, window):.0f} s of a {window['cap_s']:.0f} s cap spent; the episode's "
            f"own clock stays at {episode_s:.0f} s")


def cap_line(home, window: dict) -> str:
    return (f"CAP repair: {spent(home, window):.0f} s of the repair's {window['cap_s']:.0f} s cap spent; "
            f"every rung and costly check is cut, the owed steps run")


def close(home, now=time.time) -> dict | None:
    """The drive ended: the window's row goes to repair.jsonl and the window closes; None when none."""
    window = read(home)
    if window is None:
        return None
    row = {**window, "closed_at": float(now()), "spent_s": round(spent(home, window), 1)}
    with (Path(home) / LOG).open("a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")
    (Path(home) / WINDOW).unlink(missing_ok=True)
    return row


def history(home) -> list[dict]:
    path = Path(home) / LOG
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    return [json.loads(line) for line in lines if line.strip()]


def finish_part(home) -> str:
    """The finish line's repair part: every repair run's hours, against the latest window's cap; ''
    when the episode never ran a repair."""
    total = run_clock.repair_spent(home)
    windows = ([read(home)] if read(home) else []) or history(home)[-1:]
    if total <= 0 or not windows:
        return ""
    return f" | repair {total / 3600:.2f} h of a {windows[-1]['cap_s'] / 3600:.2f} h cap"
