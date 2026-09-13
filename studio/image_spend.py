"""The IMAGE money ledger: one line per paid image call, in the book folder.

Separate from `studio.spend`, which is the LLM usage ledger keyed by a database
connection; the two were briefly one file and the collision broke analysis.py.

`library/<book>/spend.jsonl` -- model, size, quality, count, purpose, an
ESTIMATE in USD, and the time.  The estimate is priced from the owner's
pasted table (gpt-image-2.5-sunburst: $30 per million output tokens) and
OpenAI's image token table (a high 1024x1536 is ~6.2k tokens); the exact
figure lives on the OpenAI usage page.  Owner's ask, 2026-09-10: "track all
money we spent".
"""
from __future__ import annotations

import json
import time
from pathlib import Path

ESTIMATES = {("gpt-image-2.5-sunburst", "high"): {"1024x1536": 0.08, "1536x1024": 0.08, "2048x2048": 0.13, "2048x3072": 0.20}}
"""CALIBRATED 2026-09-10 against the OpenAI usage page: $5.12 for the week,
almost all on Sep 10-11 UTC, covering ~38 image calls (26 sheets at
2048x3072, 3 stills, 1 panel, ~6 morning sheets since deleted) plus the
day's text calls.  The earlier token-table figure ($0.75 a sheet) was ~4x
too high.  Still an estimate: the exact number is the usage page."""
BASE = ("1024x1536", 0.08)


def estimate_usd(model: str, size: str, quality: str) -> float:
    table = ESTIMATES.get((model, quality), {})
    if size in table:
        return table[size]
    w, h = (int(v) for v in size.split("x"))
    bw, bh = (int(v) for v in BASE[0].split("x"))
    return round(BASE[1] * (w * h) / (bw * bh), 2)


def record(book: Path, model: str, size: str, quality: str, n: int, purpose: str) -> dict:
    row = {"at": time.strftime("%Y-%m-%d %H:%M"), "model": model, "size": size, "quality": quality,
           "n": n, "purpose": purpose, "usd_estimate": round(estimate_usd(model, size, quality) * n, 2)}
    with open(Path(book) / "spend.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")
    return row


def total(book: Path) -> float:
    path = Path(book) / "spend.jsonl"
    if not path.exists():
        return 0.0
    return round(sum(json.loads(l)["usd_estimate"] for l in path.read_text(encoding="utf-8").splitlines() if l), 2)
