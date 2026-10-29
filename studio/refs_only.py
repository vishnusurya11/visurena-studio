"""Shots whose take renders from the reference sheets only (owner ruling 2026-10-11).

    storyboard/refs_only.json    {"shots": [16], "why": {"16": "stacked after its isolate"}}

A storyboard panel still seamed or stacked after its one isolate (the panel
ladder's seam rung) is never staged: a staged doubled cell is a duplicate-figure
source (R2_verdict §0.5). The take is given the cast sheets, the place picture
and the words, ships unattended, and the panel eye's terminal flags it in the
audit sheet. The take builder, the coherence measure and the still terminal all
read this one file.
"""
from __future__ import annotations

import json
from pathlib import Path

FILE = Path("storyboard") / "refs_only.json"


def read(home: Path) -> set[int]:
    """The shots that stage no panel; empty when the file is absent."""
    path = Path(home) / FILE
    if not path.exists():
        return set()
    return {int(i) for i in json.loads(path.read_text(encoding="utf-8")).get("shots", [])}


def add(home: Path, shots: list[int], why: str) -> Path:
    """Add shots (idempotent), each with the reason it stages no panel."""
    path = Path(home) / FILE
    doc = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"shots": [], "why": {}}
    for i in shots:
        if int(i) not in doc["shots"]:
            doc["shots"].append(int(i))
        doc.setdefault("why", {})[str(int(i))] = why
    doc["shots"].sort()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=1), encoding="utf-8")
    return path


def passing(home: Path) -> set[int]:
    """The shots both panel checks passed in their last verdicts (panel_dq.json and panel_content.json)."""
    board = Path(home) / "storyboard"
    rows = []
    for name in ("panel_dq.json", "panel_content.json"):
        path = board / name
        if not path.exists():
            return set()
        rows.append({int(r["shot"]): bool(r.get("passed")) for r in json.loads(path.read_text(encoding="utf-8"))})
    return {s for s, ok in rows[0].items() if ok and rows[1].get(s)}


def lift_passing(home: Path) -> list[int]:
    """Take off the list every shot whose panel now passes both checks (Jekyll ep06 retro, 2026-10-29: panels
    24/25 were redrawn and passed, and their takes kept rendering from the bare place picture).  Off the list,
    the take's build stages its panel again and take currency reads the panel-less take as stale.  The lifted
    shots, in order; each lift recorded under `lifted`."""
    path = Path(home) / FILE
    if not path.exists():
        return []
    doc = json.loads(path.read_text(encoding="utf-8"))
    lifted = sorted(set(doc.get("shots", [])) & passing(home))
    if lifted:
        doc["shots"] = [s for s in doc["shots"] if s not in lifted]
        for s in lifted:
            doc.setdefault("lifted", {})[str(s)] = f"passed both panel checks again (was: {doc.get('why', {}).get(str(s), '')})"
        path.write_text(json.dumps(doc, indent=1), encoding="utf-8")
    return lifted
