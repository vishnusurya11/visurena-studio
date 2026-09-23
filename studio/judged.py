"""Which rendered takes have no current verdict.

QC and the upload both used to count only the T*.dq.json reports that exist,
so a take rendered and never judged -- or re-rendered after it was judged --
was not counted at all, and the publish gate could not see it (audit
2026-09-22, item 6). The universe is the takes the render recorded.
"""
from __future__ import annotations

import json
from pathlib import Path


def unjudged_takes(take_dir: Path, kinds: tuple[str, ...] = ("dq",)) -> list[str]:
    """Take names in shots.json missing any of the `kinds` of verdict
    (T<NN>.<kind>.json), or holding one older than the take itself."""
    sheet = Path(take_dir) / "shots.json"
    if not sheet.exists():
        return ["no shots.json: no record of which takes exist"]
    return [name for name in (f"T{r['index']:02d}" for r in json.loads(sheet.read_text(encoding="utf-8")))
            if any(_stale(Path(take_dir), name, kind) for kind in kinds)]


def _stale(take_dir: Path, name: str, kind: str) -> bool:
    """No verdict of this kind for this take, or one older than the take."""
    take, report = take_dir / f"{name}.mp4", take_dir / f"{name}.{kind}.json"
    return not report.exists() or (take.exists() and take.stat().st_mtime > report.stat().st_mtime)
