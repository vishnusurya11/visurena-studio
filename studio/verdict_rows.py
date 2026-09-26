"""The verdict files as rows on the Command Center's tables (decision
2026-09-25, "States": a signature is columns on the step's chip and a gate in
the order's `verdicts` JSON; `flagged` is a COUNT on a done row).

Reads only.  `db.project_event` calls in when a step completes; `studio.py
verify` (C7) asks `stale_gates` whether a done unit's signatures still name
the artefacts as they stand.  The file names come from manifest.VERDICTS and
the hashing from the signers themselves (plan_verdict, refs_verdict,
eye_verdict); nothing here re-derives either.  Every path is book-relative
posix; the absolute root is the caller's `book_dir` and is never stored.
"""
from __future__ import annotations

import json
from pathlib import Path

from studio import audit_rows, eye_verdict, manifest, plan_verdict, refs_verdict, registry
from studio.judged_gate import sha8_of

SIGNS = {"PLAN": "episodes/{unit}/plan.json",
         "LOOK": "refs/pack.jsonl",
         "EYE_PANELS": "episodes/{unit}/storyboard/shot_*.png",
         "EYE_TAKES": "episodes/{unit}/takes/r2v/T??.mp4",
         "MASTER": "episodes/{unit}/cut/master_r2v.mp4"}
"""What each gate's sha8 names: the bytes a signature binds to, as the registry
declares them (a test holds the two together)."""


def latest(book_dir: Path, pattern: str, unit: str) -> str | None:
    """The newest file the pattern names for this unit, book-relative; None
    while nothing is signed.  An eye folder keeps every signature it ever had
    (one eye_<sha8>.json per set of pictures); the step just wrote the newest."""
    book = Path(book_dir)
    found = manifest.matched(book, [pattern.replace("{unit}", unit)])
    if not found:
        return None
    return max(found, key=lambda rel: ((book / rel).stat().st_mtime, rel))


def read_row(book_dir: Path, gate: str, rel: str) -> dict:
    """One gate's entry for the order's verdicts JSON: the manifest's reading
    of the file (signer, word, rung), the sha8 it binds to, its fault count."""
    row = manifest.read_verdict(book_dir, gate, rel)
    doc = json.loads((Path(book_dir) / rel).read_text(encoding="utf-8"))
    return {"word": row.word, "by": row.signed_by, "terminal": row.terminal,
            "sha8": sha8_of(Path(book_dir) / rel), "faults": len(doc.get("faults") or []),
            "path": rel}


def step_rows(book_dir: Path, stage: str, step_id: str, unit: str) -> dict[str, dict]:
    """{gate: row} for the gates a step signs, from the newest file of each; a
    gate with no file yet is absent.  A file that will not read (half written,
    not JSON) is skipped: the projection never fails the event it rides on."""
    out: dict[str, dict] = {}
    for gate, pattern in manifest.gates_of(stage, step_id):
        rel = latest(book_dir, pattern, unit)
        if rel is None:
            continue
        try:
            out[gate] = read_row(book_dir, gate, rel)
        except (OSError, ValueError):
            continue
    return out


def flags(book_dir: Path, unit: str) -> int:
    """The unit's flags: its audit rows, one per terminal rung; 0 when the
    sheet is absent or will not read."""
    try:
        return sum(row.unit == unit for row in audit_rows.load(book_dir))
    except (OSError, ValueError):
        return 0


def deliverable(book_dir: Path, stage: str, unit: str) -> str | None:
    """The department's deliverable as it stands on disk, book-relative; None
    until the last step has written it."""
    pattern = registry.deliverable_of(stage, unit)
    found = manifest.matched(book_dir, [pattern]) if pattern else []
    return found[0] if found else None


def artefact_sha8(book_dir: Path, gate: str, unit: str) -> str:
    """The word the gate would sign NOW, by the signer's own hasher: the plan's
    bytes, the pack's, the pictures' fingerprint, the master's; '' when there
    is nothing on disk to sign."""
    book = Path(book_dir)
    files = [book / rel for rel in manifest.matched(book, [SIGNS[gate].replace("{unit}", unit)])]
    if not files:
        return ""
    if gate == "PLAN":
        return plan_verdict.plan_sha8(files[0])
    if gate == "LOOK":
        return refs_verdict.pack_sha8(book)
    if gate == "MASTER":
        return manifest.sha8_of(files[0])
    return eye_verdict.fingerprint(files)


def stale_gates(book_dir: Path, unit: str, verdicts: dict) -> list[str]:
    """The gates whose recorded sha8 no longer names the artefact as it stands.
    A record with no sha8 (an owner's rubric) cannot go stale."""
    return [gate for gate, rec in verdicts.items()
            if gate in SIGNS and rec.get("sha8")
            and rec["sha8"] != artefact_sha8(book_dir, gate, unit)]
