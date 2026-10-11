"""Per-take phases (R2_S #5, R2_verdict §2.2, 2026-10-11): the take step's clock.

    encode_s          execution_start -> 'Requested to load MiniMaxH3' (TE + ref encode, loads)
    first_step_gap_s  that load request -> the sampler's 0/N bar (patching, upload)
    sample_s, s_per_it, steps   the last finished N/N it-bar inside the window
    decode_save_s     the finished bar -> execution_success (VAE decodes, CreateVideo, SaveVideo)
    unet_reran, te_reran        the UNETLoader / CLIPLoader node absent from execution_cached

The bar is read from ComfyUI's timestamped log ring (`/internal/logs/raw`, 300
entries): the live engine's comfyui.log was overwritten by a failed second launch
on 2026-10-10, so a file is not a source.  A ring that already lost the take
records what history knows and leaves the bar's fields None -- never a guess.
"""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

BAR = re.compile(r"(?<![\w:])(\d+)/(\d+) \[(\d+):(\d+)<[^,\]]*,\s*([\d.]+)(s/it|it/s)\]")
BAR_START = re.compile(r"\b0/(\d+) \[")
LOAD = "Requested to load MiniMaxH3"


def stamp(entry: dict) -> float:
    return datetime.fromisoformat(entry["t"]).timestamp()


def window(record: dict) -> tuple[float | None, float | None]:
    msgs = record.get("status", {}).get("messages", [])
    t0 = next((m[1].get("timestamp") for m in msgs if m[0] == "execution_start"), None)
    t1 = next((m[1].get("timestamp") for m in msgs if m[0] in ("execution_success", "execution_error")), None)
    return (t0 / 1000 if t0 else None), (t1 / 1000 if t1 else None)


def inside(entries: list[dict], t0: float, t1: float) -> list[tuple[float, str]]:
    return [(stamp(e), e.get("m", "")) for e in entries if t0 <= stamp(e) <= t1]


def bar(lines: list[tuple[float, str]]) -> dict:
    """The last finished it-bar: steps, seconds, s/it and when it flushed."""
    found = {}
    for t, m in lines:
        for b in BAR.finditer(m):
            if b.group(1) == b.group(2):
                rate = float(b.group(5))
                found = {"steps": int(b.group(2)), "sample_s": int(b.group(3)) * 60 + int(b.group(4)),
                         "s_per_it": round(rate if b.group(6) == "s/it" else 1 / rate, 3), "at": t}
    return found


def first(lines: list[tuple[float, str]], hit) -> float | None:
    return next((t for t, m in lines if hit(m)), None)


def reran(record: dict, cls: str) -> bool | None:
    """Did the node of class `cls` execute (not served from cache)?"""
    graph = (record.get("prompt") or [None, None, {}])[2]
    ids = [k for k, n in graph.items() if n.get("class_type") == cls]
    cached = {n for m in record.get("status", {}).get("messages", []) if m[0] == "execution_cached"
              for n in m[1].get("nodes", [])}
    return any(k not in cached for k in ids) if ids else None


def gap(a: float | None, b: float | None) -> float | None:
    return round(b - a, 1) if a is not None and b is not None else None


def phases(record: dict, entries: list[dict]) -> dict:
    """One take's phase row from its history record and the log ring."""
    t0, t1 = window(record)
    lines = inside(entries, t0, t1) if t0 and t1 else []
    b, load = bar(lines), first(lines, lambda m: LOAD in m)
    start = first(lines, lambda m: bool(BAR_START.search(m)) and "tile" not in m)
    return {"prompt_s": gap(t0, t1), "encode_s": gap(t0, load), "first_step_gap_s": gap(load, start),
            "steps": b.get("steps"), "sample_s": b.get("sample_s"), "s_per_it": b.get("s_per_it"),
            "decode_save_s": gap(b.get("at"), t1),
            "unet_reran": reran(record, "UNETLoader"), "te_reran": reran(record, "CLIPLoader")}


def ring() -> list[dict]:
    """ComfyUI's log ring; [] when the engine cannot say (the row keeps history's part)."""
    from studio.comfy import HOST
    import urllib.request
    try:
        with urllib.request.urlopen(f"{HOST}/internal/logs/raw", timeout=10) as r:
            return json.loads(r.read()).get("entries", [])
    except Exception:
        return []


def record(video: Path, take: dict, history: dict, entries: list[dict] | None = None) -> dict:
    """Append this take's phases to phases.jsonl beside its video."""
    row = {"take": take.get("index"), "video": Path(video).name,
           **phases(history, ring() if entries is None else entries)}
    with (Path(video).parent / "phases.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row) + "\n")
    return row
