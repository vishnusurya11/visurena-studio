"""The spans of an episode, folded from every run it ever had (Jekyll Kawajiri ep01, 2026-10-19).

The card read state by position -- the newest run -- so the 19:28 rewind blanked steps 08 and 09,
and a sum of timing rows charged a `takes` row of -421.1 s (take_dq and face_refine ran beside the
render).  A span is read from the step MARKERS, never from a sum of rows: a `step_NN started` row
opens it, the work rows after it stretch its end, the next marker closes it.  A row with negative
seconds adds nothing.  One reader serves old episodes (timing.jsonl) and new ones (progress.jsonl)."""
from __future__ import annotations

import json
import re
from pathlib import Path

from studio import eta, progress

STEP_ROW = re.compile(r"step_(\d\d)$")
KILLED_AFTER_S = 60.0
"""A workless span is a dead attempt only when the next marker came a minute or more later."""
CLOSING = ("done", "skip", "fail", "deferred", "refused", "escalated")


def read_rows(path: Path) -> list[dict]:
    """The JSON object lines of a jsonl file; torn lines and a missing file give nothing."""
    try:
        lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []
    out = []
    for line in lines:
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if isinstance(row, dict):
            out.append(row)
    return out


def clean(rows: list[dict]) -> list[dict]:
    """The rows that can be charged: objects whose seconds are not negative."""
    return [r for r in rows if isinstance(r, dict) and float(r.get("seconds") or 0.0) >= 0.0]


def _open(spans: list[dict], step: str, t0: float) -> dict:
    span = {"step": step, "start": t0, "end": t0}
    spans.append(span)
    return span


def spans(rows: list[dict], since: float | None = None) -> list[dict]:
    """[{step, start, end}] in marker order; work rows stretch the open span's end."""
    out, cur = [], None
    for r in clean(rows):
        t0 = eta.to_epoch(r.get("started"))
        if t0 is None or (since and t0 < since - 5):
            continue
        m = STEP_ROW.match(str(r.get("stage") or ""))
        if m and r.get("event") == "started":
            cur = _open(out, m.group(1), t0)
        elif cur is not None:
            cur["end"] = max(cur["end"], eta.to_epoch(r.get("ended")) or t0)
    return out


def total_of(found: list[dict]) -> dict[str, dict]:
    """{step: {secs, end, n}}: a step's spans summed, its last end, its attempts."""
    out: dict[str, dict] = {}
    for s in found:
        a = out.setdefault(s["step"], {"secs": 0.0, "end": s["end"], "n": 0})
        a["secs"], a["end"], a["n"] = a["secs"] + s["end"] - s["start"], max(a["end"], s["end"]), a["n"] + 1
    return out


def totals(rows: list[dict], since: float | None = None) -> dict[str, dict]:
    """The per-step totals of timing rows."""
    return total_of(spans(rows, since))


def rewinds(rows: list[dict]) -> list[dict]:
    """[{t, frm, to}]: a step that starts after a LATER step did work.  A span with no work after
    its marker is an attempt that died, so the next marker restarts it and rewinds nothing."""
    found, out = spans(rows), []
    for prev, now in zip(found, found[1:]):
        if prev["end"] > prev["start"] and int(prev["step"]) > int(now["step"]):
            out.append({"t": now["start"], "frm": prev["step"], "to": now["step"]})
    return out


def from_progress(events: list[dict]) -> dict[str, dict]:
    """The totals of progress.jsonl `step` events: a start opens a span, a closing state ends it."""
    found, cur = [], {}
    for ev in events:
        if ev.get("ev") != "step" or ev.get("t") is None:
            continue
        sid, t = str(ev.get("step")), float(ev["t"])
        if ev.get("state") == "start":
            cur[sid] = _open(found, sid, t)
        elif ev.get("state") in CLOSING and sid in cur:
            cur.pop(sid)["end"] = t
    return total_of(found)


def fold_home(home: Path) -> dict[str, dict]:
    """The episode's totals: progress.jsonl when it holds step events, else timing.jsonl."""
    home = Path(home)
    new = from_progress(progress.read_events(home / "progress.jsonl"))
    if new:
        return new
    return totals(read_rows(home / "timing.jsonl"))


def killed(rows: list[dict]) -> list[dict]:
    """[{step, start, secs}]: an attempt that did no work and was followed by another marker --
    a dead run, priced to the next marker (the 89 min from step 10's hang to its relaunch)."""
    found, out = spans(rows), []
    for span, after in zip(found, found[1:]):
        if span["end"] == span["start"] and after["start"] - span["start"] >= KILLED_AFTER_S:
            out.append({"step": span["step"], "start": span["start"], "secs": after["start"] - span["start"]})
    return out
