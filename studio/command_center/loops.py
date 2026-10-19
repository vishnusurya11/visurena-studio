"""The loops of a run, as they are (timeline debate 2026-10-18, D1; owner go).

The runner never steps back inside a run (0 regressions in 3,253 events). A loop is either
work a later step runs on behalf of an earlier one inside its own wall -- 08 redraws 07's grids,
11 re-runs 09's takes -- found by timing.jsonl's work names (eta.SUB_STEP) inside a later step's
span, or a relaunch that enters an earlier step, found in the events table by run. Pure reads;
no arrows: every mark names who did whose work."""
from __future__ import annotations

import re
from collections.abc import Callable

from studio import eta

STEP_ROW = re.compile(r"step_(\d\d)$")
ENDS = ("completed", "skipped", "failed", "deferred", "escalated", "started")


def borrowed(rows: list[dict], since: float | None = None) -> list[dict]:
    """[{host, owner, sub, n, secs}]: an earlier step's work run inside a later step's span."""
    host, acc = None, {}
    for r in rows:
        t0 = eta.to_epoch(r.get("started"))
        if t0 is None or (since and t0 < since - 5):
            continue
        m = STEP_ROW.match(str(r.get("stage") or ""))
        if m:
            host = m.group(1)
            continue
        owner = eta.SUB_STEP.get(str(r.get("stage")))
        if host and owner and owner < host:
            a = acc.setdefault((host, owner, r["stage"]), [0, 0.0])
            a[0], a[1] = a[0] + 1, a[1] + float(r.get("seconds") or 0.0)
    return [{"host": h, "owner": o, "sub": s, "n": n, "secs": secs} for (h, o, s), (n, secs) in acc.items()]


def span_words(secs: float) -> str:
    """`17m` / `1h05` / `<1m`."""
    m = int(secs // 60)
    return f"{m // 60}h{m % 60:02d}" if m >= 60 else (f"{m}m" if m else "<1m")


def loop_words(b: dict) -> str:
    """`08 re-ran 07's grids ×2 · 17m`."""
    return f"{b['host']} re-ran {b['owner']}'s {b['sub']} ×{b['n']} · {span_words(b['secs'])}"


def attempts(db_rows: list[dict], runs: set[str] | None = None) -> list[dict]:
    """Each run of the unit in order: the step it entered at, its last step and how it stood."""
    by: dict[str, dict] = {}
    for r in db_rows:
        rid = r.get("run_id")
        if not rid or (runs is not None and rid not in runs) or r.get("event") not in ENDS:
            continue
        a = by.setdefault(rid, {"run": rid, "entered": str(r["step_id"]), "last": None, "how": None, "at": None})
        a["last"], a["how"], a["at"] = str(r["step_id"]), r["event"], r.get("event_ts")
    return list(by.values())


def loops_text(runs: list[dict], work: list[dict], clock: Callable[[float | None], str] = lambda t: "") -> str:
    """The card's one loops line: the relaunch, then each step's work for an earlier step."""
    parts = [attempts_words(runs, clock)] + [loop_words(b) for b in work]
    return " · ".join(p for p in parts if p)


def attempts_words(runs: list[dict], clock: Callable[[float | None], str] = lambda t: "") -> str:
    """`run 2 of 2 · entered at 06 after run 1 failed at 11 (5:12 pm)`; '' for one run."""
    if len(runs) < 2:
        return ""
    cur, prev = runs[-1], runs[-2]
    when = clock(eta.to_epoch(prev["at"])) if prev.get("at") else ""
    how = (f"stopped after {prev['last']}" if prev["how"] in ("completed", "skipped", "started")
           else f"{prev['how']} at {prev['last']}")
    return (f"run {len(runs)} of {len(runs)} · entered at {cur['entered']} after run {len(runs) - 1} {how}"
            + (f" ({when})" if when else ""))
