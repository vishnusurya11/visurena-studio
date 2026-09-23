"""Which rendered takes have no current verdict.

QC and the upload both used to count only the T*.dq.json reports that exist,
so a take rendered and never judged -- or re-rendered after it was judged --
was not counted at all, and the publish gate could not see it (audit
2026-09-22, item 6). The universe is the takes the render recorded.
"""
from __future__ import annotations

import json
from pathlib import Path


def unjudged_takes(take_dir: Path) -> list[str]:
    """Take names in shots.json with no report, or a report older than the take."""
    sheet = Path(take_dir) / "shots.json"
    if not sheet.exists():
        return ["no shots.json: no record of which takes exist"]
    out = []
    for record in json.loads(sheet.read_text(encoding="utf-8")):
        name = f"T{record['index']:02d}"
        take, report = Path(take_dir) / f"{name}.mp4", Path(take_dir) / f"{name}.dq.json"
        if not report.exists() or (take.exists() and take.stat().st_mtime > report.stat().st_mtime):
            out.append(name)
    return out
