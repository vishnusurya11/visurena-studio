#!/usr/bin/env python
"""Warp labels: which G-WARP numbers does a person's eye agree with?  (P07, 2026-10-19)

Joins `measures.warp` of the take dq records to the labels a person signed -- the casebook's
owner.jsonl and eye-patch strips signed by the owner or the master eye.  A shipped take is a
default PASS and take_eye echoes the gate, so neither is a label.  Hard Se is re-armed only
when a SUSTAINED eye run (>= 12 consecutive frame-pairs with face_w < 0.10) has >= 80 %
precision on those labels; until then Se stays the advisory `eye` (studio/warp_gate.py).

    uv run python scripts/episode/warp_labels.py <owner.jsonl> <dq.json>...   (named files only)
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

PEOPLE = ("owner", "master_eye", "person")
RUN_PAIRS = 12
FACE_W_MAX = 0.10
PRECISION_MIN = 0.80
LABELS_MIN = 5


def take_id(path: str) -> str | None:
    found = re.search(r"(T\d{2})", path or "")
    return found.group(1) if found else None


def labels(rows: list[dict]) -> dict[str, str]:
    """take -> pass / fault from the rows an owner signed; defaults, agents and take_eye are not labels."""
    got = {take_id(r.get("path", "")): r["verdict"] for r in rows if r.get("verdict_by") == "owner"}
    return {t: v for t, v in got.items() if t}


def strip_labels(strips: list[dict]) -> dict[str, str]:
    """take -> pass / fault from eye-patch strips signed by a person or the master eye."""
    return {s["take"]: s["verdict"] for s in strips if s.get("signed_by") in PEOPLE}


def join(warp_by_take: dict[str, dict], signed: dict[str, str]) -> list[dict]:
    """One row per labelled take: its label and the warp numbers the gate logged."""
    keys = ("S", "Se", "S_held", "Se_held", "face_w", "eye_spans", "frames_eye")
    return [{"take": t, "label": signed[t]} | {k: warp_by_take[t].get(k) for k in keys}
            for t in sorted(signed) if t in warp_by_take]


def sustained(m: dict) -> bool:
    """An eye run of >= 12 consecutive frame-pairs on a small face (a blink is 5-8 frames)."""
    longest = max((b - a + 1 for a, b in m.get("eye_spans") or []), default=0)
    width = m.get("face_w")
    return longest >= RUN_PAIRS and width is not None and width < FACE_W_MAX


def precision(rows: list[dict]) -> float | None:
    """Of the takes the sustained rule would fail, the share the person called a fault."""
    hit = [r for r in rows if sustained(r)]
    return sum(r["label"] == "fault" for r in hit) / len(hit) if hit else None


def rearmed(rows: list[dict]) -> bool:
    """Hard Se may return only at >= 80 % precision over at least LABELS_MIN labelled takes."""
    p = precision(rows)
    return len(rows) >= LABELS_MIN and p is not None and p >= PRECISION_MIN


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(x) for x in Path(path).read_text(encoding="utf-8").splitlines() if x.strip()]


def main(argv: list[str]) -> int:
    owner, dqs = Path(argv[0]), [Path(a) for a in argv[1:]]
    warp = {take_id(p.name): (json.loads(p.read_text(encoding="utf-8")).get("measures") or {}).get("warp") or {}
            for p in dqs}
    rows = join(warp, labels(read_jsonl(owner)))
    print(json.dumps({"labelled": len(rows), "precision": precision(rows), "rearmed": rearmed(rows)}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
