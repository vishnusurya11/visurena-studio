"""Put ComfyUI's own execution time on each Prism timing row.

    uv run python -m prism.timing        # reads /history, rewrites docs/audit/prism/timings.jsonl

The render's wall clock is quantised by the client's 5 s poll (every model read 10.1-10.2 s);
the engine's history carries execution_start and execution_success timestamps in ms.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SAVED = re.compile(r"^(?P<subject>[a-z0-9_]+?)__(?P<model>[a-z0-9_]+?)_\d+_\.png$")


def stamp(record: dict, event: str) -> int | None:
    hits = [m[1]["timestamp"] for m in record.get("status", {}).get("messages", []) if m[0] == event]
    return hits[0] if hits else None


def exec_seconds(record: dict) -> float | None:
    start, end = stamp(record, "execution_start"), stamp(record, "execution_success")
    return round((end - start) / 1000, 1) if start is not None and end is not None else None


def job_key(record: dict) -> tuple[str, str, str] | None:
    for output in record.get("outputs", {}).values():
        for image in output.get("images", []):
            folder = image.get("subfolder", "").replace("\\", "/").split("/")
            hit = SAVED.match(image.get("filename", ""))
            if hit and len(folder) == 2 and folder[0] == "prism":
                return folder[1], hit["subject"], hit["model"]
    return None


def latest_times(history: dict) -> dict[tuple, float]:
    """(style, subject, model) -> the engine time of its latest successful render."""
    ranked = sorted(history.values(), key=lambda r: stamp(r, "execution_start") or 0)
    return {job_key(r): exec_seconds(r) for r in ranked if job_key(r) and exec_seconds(r) is not None}


def backfill(rows: list[dict], history: dict) -> list[dict]:
    times = latest_times(history)
    return [{**r, "exec_seconds": times[k]} if (k := (r["style"], r["subject"], r["model"])) in times else r
            for r in rows]


def main(argv: list[str]) -> int:
    import urllib.request
    from prism.board import read_rows
    from prism.render import ROOT
    with urllib.request.urlopen("http://127.0.0.1:8188/history?max_items=5000", timeout=60) as reply:
        history = json.loads(reply.read())
    rows = backfill(read_rows(ROOT), history)
    (ROOT / "timings.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    print(f"{sum('exec_seconds' in r for r in rows)} of {len(rows)} rows carry the engine time")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
