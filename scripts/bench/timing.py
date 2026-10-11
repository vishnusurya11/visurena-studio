#!/usr/bin/env python
"""Per-render seconds from ComfyUI itself, not wall clock (P2 §3.5).

For each bench prompt: whole-prompt seconds (history execution_start..success), the
sampler's own seconds and s/it (the last `N/N [mm:ss<..., X s/it]` line the log wrote
inside that prompt's window), and decode+save = prompt end - sampler end. A render is
CONTAMINATED when a foreign prompt (another session) ran between it and the previous
bench render (its models may have been evicted), or when it is the first of a model chain.

    uv run --no-sync python scripts/bench/timing.py <comfyui.log> <runs.jsonl>... > timing.json
"""
from __future__ import annotations

import json
import re
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

STAMP = re.compile(r"\[(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d\.\d+)\]")
SAMPLER = re.compile(r"(\d+)/(\1) \[(\d+):(\d+)<[^,]*,\s*([\d.]+)s/it\]")


def log_events(text: str) -> list[tuple[float, str]]:
    """(epoch seconds, line) for every stamped line; carriage-return progress split out."""
    out, last = [], None
    for raw in text.replace("\r", "\n").splitlines():
        m = STAMP.search(raw)
        if m:  # a bar's later fragments follow a carriage return unstamped: they inherit its opening stamp
            last = datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S.%f").timestamp()
        if last is not None:
            out.append((last, raw))
    return out


def sampler_in(events: list[tuple[float, str]], t0: float, t1: float) -> dict | None:
    """The last finished sampler bar stamped inside [t0, t1]."""
    found = None
    for t, line in events:
        if t0 <= t <= t1:
            for m in SAMPLER.finditer(line):
                secs = int(m.group(3)) * 60 + int(m.group(4))
                found = {"steps": int(m.group(1)), "sample_s": secs, "s_per_it": float(m.group(5)), "at": t}  # the stamp is the flush of the finished bar
    return found


def history() -> dict:
    with urllib.request.urlopen("http://127.0.0.1:8188/history?max_items=400", timeout=60) as r:
        return json.loads(r.read())


def window(rec: dict) -> tuple[float, float] | None:
    msgs = rec.get("status", {}).get("messages", [])
    t0 = next((m[1]["timestamp"] for m in msgs if m[0] == "execution_start"), None)
    t1 = next((m[1]["timestamp"] for m in msgs if m[0] in ("execution_success", "execution_error")), None)
    return (t0 / 1000, t1 / 1000) if t0 and t1 else None


def main(log: Path, runs: list[Path]) -> None:
    mine = {}
    for p in runs:
        for line in p.read_text("utf-8").splitlines():
            r = json.loads(line)
            if "prompt_id" in r:
                mine[r["prompt_id"]] = r["tag"]
    hist = history()
    spans = sorted(((window(v), k) for k, v in hist.items() if window(v)), key=lambda x: x[0][0])
    events = log_events(log.read_text("utf-8", errors="replace"))
    out, prev_mine = {}, False
    for (t0, t1), pid in spans:
        if pid not in mine:
            prev_mine = False
            continue
        s = sampler_in(events, t0, t1) or {}
        out[mine[pid]] = {"prompt_s": round(t1 - t0, 1), **{k: v for k, v in s.items() if k != "at"},
                          "decode_save_s": round(t1 - s["at"], 1) if s else None,
                          "after_foreign_or_first": not prev_mine}
        prev_mine = True
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main(Path(sys.argv[1]), [Path(p) for p in sys.argv[2:]])
