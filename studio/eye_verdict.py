"""An eye verdict, bound to the pictures it was given.

    <dir>/eye_<sha8>.json      sha8 = the fingerprint of the pictures, sorted by name

The panel eye signs the storyboard panels; the take eye signs the kept takes.
A verdict names bytes, not a folder: redraw one panel and the fingerprint
moves, so the old signature no longer counts.  `require` is the gate a step
calls -- it parks the unit (Escalation) while no verdict exists, and refuses
(SystemExit) one that named a fault, because a fault is work to do, not a
signature to wait for.  A judge signs `pass`, or `flagged` at a terminal rung
(`sign_verdict`); the next step runs on either and refuses only `fault`.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from studio.escalate import Escalation
from studio.judges import verdict as jv

VERDICTS = ("pass", "flagged", "fault")
PASSING = ("pass", "flagged")


def fingerprint(paths: list[Path]) -> str:
    """sha8 of the files' bytes, concatenated in name order: the same set of
    pictures gives the same word whatever order it was listed in."""
    digest = hashlib.sha256()
    for p in sorted(Path(p) for p in paths):
        digest.update(p.read_bytes())
    return digest.hexdigest()[:8]


def path(folder: Path, sha8: str) -> Path:
    return Path(folder) / f"eye_{sha8}.json"


def current(folder: Path, paths: list[Path]) -> dict | None:
    """The verdict signed for exactly these pictures, or None."""
    target = path(folder, fingerprint(paths))
    if not target.exists():
        return None
    return json.loads(target.read_text(encoding="utf-8"))


def passed(folder: Path, paths: list[Path]) -> bool:
    """Whether a current verdict says pass or flagged: a flag is a signature
    with its faults on record, never a park."""
    verdict = current(folder, paths)
    return bool(verdict) and verdict.get("verdict") in PASSING


def require(folder: Path, paths: list[Path], gate: str, ask: str, home: Path | None = None) -> dict:
    """The current verdict, or the gate raised: an Escalation naming the file
    (relative to `home`, else to the folder's parent) while none exists, a
    refusal when the owner named a fault."""
    verdict = current(folder, paths)
    if verdict is None:
        target = path(folder, fingerprint(paths))
        rel = target.relative_to(Path(home) if home else Path(folder).parent).as_posix()
        raise Escalation(gate, rel, ask)
    if verdict.get("verdict") not in PASSING:
        raise SystemExit(f"REFUSED: the eye named a fault: {verdict.get('note', '')}")
    return verdict


def sign(folder: Path, paths: list[Path], verdict: str, note: str, *,
         signed_by: str = jv.OWNER, faults: list[dict] | None = None, terminal: str = "") -> Path:
    """Write the verdict for these pictures.  A verdict is pass, flagged or
    fault, and it carries a note: a signature with nothing said is the
    six-frame glance.  A judge's hand adds who signed, the faults, the rung."""
    if verdict not in VERDICTS:
        raise SystemExit(f"a verdict is one of {VERDICTS}, not {verdict!r}")
    if not note.strip():
        raise SystemExit("say what was seen: the note may not be empty")
    sha8 = fingerprint(paths)
    doc = {"sha8": sha8, "verdict": verdict, "note": note.strip(),
           "files": [Path(p).name for p in sorted(Path(p) for p in paths)],
           "signed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           **jv.signature(signed_by, faults, terminal=terminal)}
    target = path(folder, sha8)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
    return target


def sign_verdict(folder: Path, paths: list[Path], v: jv.Verdict) -> Path:
    """The judge's entry: a pass, or a flag at a terminal rung; never a fault."""
    return sign(folder, paths, jv.word(v), v.summary(), signed_by=v.signer,
                faults=[f.model_dump() for f in v.faults], terminal=v.terminal)
