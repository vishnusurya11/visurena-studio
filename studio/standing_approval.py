"""The owner's standing hand at the publish door: one file per book.

Ruling 2026-10-01 ("no human input at publish"): judge-signed terminals clear
the lock and the upload runs unattended.  That ruling is the owner's standing
approval in prose; `library/<book>/publish/standing.json` is the same hand in
a form a step can read -- written ONCE per book, by the owner, never by code:

    {"kind": "publish", "decision": "2026-10-01-no-human-input-at-publish",
     "by": "<owner>", "at": "<date>"}

With it, step 13 appends `--approved=publish` to the upload and the privacy
flip (studio/approval.py is untouched; RENDER_HOLD still stops everything
first).  Absent or malformed, the step parks its unit with an Escalation
(G-STANDING) and nothing uploads.
"""
from __future__ import annotations

import json
from pathlib import Path

from studio.escalate import Escalation

DECISION = "2026-10-01-no-human-input-at-publish"
FILE = "publish/standing.json"


def path(book) -> Path:
    return Path(book) / "publish" / "standing.json"


def read(book) -> dict:
    """The file's claim, or {} -- a malformed file approves nothing."""
    try:
        said = json.loads(path(book).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return said if isinstance(said, dict) else {}


def ok(book) -> bool:
    """The kind, the exact decision id, and a named owner: all three or no."""
    said = read(book)
    return (said.get("kind") == "publish" and said.get("decision") == DECISION
            and bool(str(said.get("by", "")).strip()))


def escalation(book) -> Escalation:
    """What the owner is asked to write, once, and where the signature goes."""
    return Escalation("G-STANDING", FILE,
                      'write the standing publish approval once for this book: '
                      f'{{"kind": "publish", "decision": "{DECISION}", '
                      f'"by": "<owner>", "at": "<date>"}}')
