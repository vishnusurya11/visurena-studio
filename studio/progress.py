"""The episode progress channel's reader (progress tracker spec §1).

`library/<book>/episodes/epNN/progress.jsonl` is append-only, one JSON event
per line: `step` (start|done|skip|fail|deferred|refused|escalated), `sub`,
`plan` (items + kept), `item` (done|fail), `round` (one ladder rung) and
`end` (the outcome).  `fold()` turns a stream of them into the state the
board's live card draws.

v1 has no writer yet (W1-W7 land between episodes): the board derives the
same events from the files a run already writes
(`studio/command_center/legacy_progress.py`) and folds them here, so v2 swaps
the source and keeps this function."""
from __future__ import annotations

import json
from pathlib import Path


def read_events(path: Path) -> list[dict]:
    """The file's events in order; a torn or foreign line is skipped, a missing file is empty."""
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    out = []
    for line in text.splitlines():
        try:
            ev = json.loads(line)
        except ValueError:
            continue
        if isinstance(ev, dict) and ev.get("ev"):
            out.append(ev)
    return out


def empty() -> dict:
    """The state before any event."""
    return {"run": None, "t0": None, "last_t": None, "steps": {}, "step": None, "step_t": None,
            "sub": None, "plan": [], "kept": [], "plan_t": None, "done": {}, "fresh": [], "landed": {},
            "failed": [], "rounds": [], "outcome": None}


def _step(s: dict, ev: dict) -> None:
    sid = str(ev.get("step"))
    s["steps"][sid] = {"name": ev.get("name") or s["steps"].get(sid, {}).get("name", ""),
                       "state": ev.get("state"), "t": ev.get("t")}
    if ev.get("state") == "start":
        s["step"], s["step_t"], s["sub"] = sid, ev.get("t"), None
    elif s["step"] is None or sid >= s["step"]:
        s["step"] = sid


def _plan(s: dict, ev: dict) -> None:
    s["plan"] = [[str(i), w] for i, w in ev.get("items") or []]
    s["kept"] = [str(i) for i in ev.get("kept") or []]
    s["plan_t"], s["fresh"], s["failed"] = ev.get("t"), [], []


def _item(s: dict, ev: dict) -> None:
    item = str(ev.get("item"))
    if ev.get("state") == "fail":
        s["failed"].append(item)
        return
    s["done"].setdefault(item, []).append(ev.get("secs"))
    s["fresh"].append(item)
    if ev.get("t") is not None:
        s["landed"][item] = ev.get("t")


def _round(s: dict, ev: dict) -> None:
    s["rounds"].append({k: ev.get(k) for k in ("t", "gate", "measured", "threshold", "action", "terminal")})


APPLY = {"step": _step, "plan": _plan, "item": _item, "round": _round,
         "sub": lambda s, ev: s.update(sub=ev.get("sub") if ev.get("state") == "start" else None),
         "end": lambda s, ev: s.update(outcome=ev.get("outcome"))}


def fold(events: list[dict]) -> dict:
    """The state after every event, in order.  The run starts at its first
    step-side event; a ladder rung (another log's clock) never moves it."""
    s = empty()
    for ev in events:
        t = ev.get("t")
        if t is not None:
            if ev.get("ev") != "round":
                s["t0"] = t if s["t0"] is None else min(s["t0"], t)
            s["last_t"] = t if s["last_t"] is None else max(s["last_t"], t)
        s["run"] = ev.get("run") or s["run"]
        if ev.get("ev") in APPLY:
            APPLY[ev["ev"]](s, ev)
    return s


def counts(state: dict) -> tuple[int, int, float, float]:
    """(done, total, weight done, weight total) of the current plan; kept items count as done."""
    have = set(state["kept"]) | set(state["fresh"])
    done = [w for i, w in state["plan"] if i in have]
    return len(done), len(state["plan"]), sum(done), sum(w for _, w in state["plan"])


def item_state(state: dict, item: str) -> str:
    """waiting | landed | retake | failed for one planned item (rendering is the view's call)."""
    if item in state["failed"] and item not in state["fresh"]:
        return "failed"
    if len(state["done"].get(item, [])) > 1 and item in state["fresh"]:
        return "retake"
    return "landed" if item in state["kept"] or item in state["fresh"] else "waiting"
