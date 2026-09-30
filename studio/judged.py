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
    """No verdict of this kind for this take, or one about other bytes.  A
    verdict naming the take's exact bytes (take_sha8) is current whatever the
    clocks say: ep14 (2026-09-30) re-rendered identical bytes, the byte-cache
    kept the report, and the mtime rule called a judged take unjudged."""
    take, report = take_dir / f"{name}.mp4", take_dir / f"{name}.{kind}.json"
    if not report.exists():
        return True
    if not take.exists() or take.stat().st_mtime <= report.stat().st_mtime:
        return False
    import hashlib
    import json
    try:
        said = json.loads(report.read_text(encoding="utf-8")).get("take_sha8")
    except (ValueError, OSError):
        return True
    return said != hashlib.sha256(take.read_bytes()).hexdigest()[:8]
