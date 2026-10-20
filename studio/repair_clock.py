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
the drive continues it.  A window a killed drive left open is closed at the next drive's start unless
the repair is still owed (`backed`: the owner's receipt stands, or its step completed and step 12 has not
delivered again; incident 2026-10-19 11:18 PDT).  A redo of 09 or later re-renders no delivered take, in
the window and after it (take_currency.frozen reads the open window, else the latest closed row).  Its budget is charged with the repair-tagged run spans since it opened
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
    write(home, window)
    return window


def write(home, window: dict) -> None:
    """repair.json, atomically."""
    path = Path(home) / WINDOW
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(window), encoding="utf-8")
    os.replace(tmp, path)


def window_for(conn, home, started: float | None) -> dict | None:
    """The window this drive runs in: the open one (adopting a newer owner order for its steps), else
    one opened now for an owner redo of a delivered episode, else None (a normal run, on the 6 h)."""
    if (window := read(home)) is not None:
        return adopt(home, window, work_orders.owner_receipts(conn, home))
    orders = work_orders.owner_receipts(conn, home)
    if not orders or not delivered(home):
        return None
    return open_window(home, orders, started)


def adopt(home, window: dict, receipts: dict[str, int]) -> dict:
    """A second owner order for a step the open window names, taken by the runner after the drive's
    start, becomes the window's order (same opening, same cap): the next drive's start backs it."""
    newer = {s: oid for s, oid in receipts.items() if s in (window.get("orders") or {})
             and oid != int(window["orders"][s])}
    if not newer:
        return window
    window = {**window, "orders": {**window["orders"], **newer}}
    write(home, window)
    return window


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


def close(home, now=time.time, why: str = "") -> dict | None:
    """The drive ended: the window's row goes to repair.jsonl and the window closes; None when none.
    `why` names a close that is not its drive's end (`closed_by`)."""
    window = read(home)
    if window is None:
        return None
    row = {**window, "closed_at": float(now()), "spent_s": round(spent(home, window), 1)}
    row |= {"closed_by": why} if why else {}
    with (Path(home) / LOG).open("a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")
    (Path(home) / WINDOW).unlink(missing_ok=True)
    return row


UNBACKED = ("drive start: no owner receipt backs it and no step it redid is still owed (a drive that never "
            "reached its end left it open)")


def backed(conn, home, window: dict) -> bool:
    """The repair is still owed: every order the window names is an OWNER redo whose receipt still
    stands (K12), or whose step completed (receipt cleared) while the episode has not been delivered
    again since the window opened (fix round 2026-10-19: a drive killed in 10-12).  A receipt naming
    another order backs nothing."""
    orders = {k: int(v) for k, v in (window.get("orders") or {}).items()}
    if not orders or work_orders.owner_ids(conn, orders.values()) != set(orders.values()):
        return False
    taken, again = work_orders.receipts(home), redelivered(home, window)
    return all(taken.get(step) == oid or (step not in taken and not again) for step, oid in orders.items())


def redelivered(home, window: dict) -> bool:
    """Step 12 wrote the manifest again after the window opened: the repair delivered."""
    path = Path(home) / "manifest.json"
    return path.exists() and path.stat().st_mtime >= float(window["opened_at"])


def close_unbacked(conn, home, now=time.time) -> dict | None:
    """At a drive's start (ship review minor 1, incident 2026-10-19): a leftover window no owner receipt
    backs is closed into repair.jsonl, never reused; a backed one is the same owed order and holds."""
    window = read(home)
    if window is None or backed(conn, home, window):
        return None
    return close(home, now, UNBACKED)


def history(home) -> list[dict]:
    path = Path(home) / LOG
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    return [json.loads(line) for line in lines if line.strip()]


def finish_part(home) -> str:
    """The finish line's repair part: each repair window's hours against its OWN cap, the redone steps
    named when there are several; '' when the episode never ran a repair.  Deadline retro 2026-10-20:
    ep01's line summed two repairs against the second cap ("1.83 h of a 0.63 h cap"); each stayed inside
    its own (5,788 of 8,580 s, 790 of 2,280 s)."""
    parts = [(row["spent_s"], row) for row in history(home)]
    parts += [(spent(home, w), w) for w in [read(home)] if w]
    if sum(s for s, _ in parts) <= 0:
        return ""
    named = len(parts) > 1
    return " | repair " + ", ".join(f"{s / 3600:.2f} h of a {w['cap_s'] / 3600:.2f} h cap"
                                    + (f" ({','.join(w['steps'])})" if named else "") for s, w in parts)
