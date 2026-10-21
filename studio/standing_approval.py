"""The owner's standing hand at the publish door: one file per book.

Ruling 2026-10-01 ("no human input at publish"): judge-signed terminals clear
the lock and the upload runs unattended.  That ruling is the owner's standing
approval in prose; `library/<book>/publish/standing.json` is the same hand in
a form a step can read -- written ONCE per book, by the owner, never by code:

    {"kind": "publish", "decision": "2026-10-01-no-human-input-at-publish",
     "by": "<owner>", "at": "<date>", "episodes": [1, 2]}

`episodes` lists the masters the owner asked to upload (rule 2026-10-12, "no
upload unless asked"; five-iterations build B1.3, 2026-10-20): the Jekyll file
signed for ep01 approved every later chapter too.  An unlisted episode parks.

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


def listed(said: dict) -> set[int]:
    """The episodes the file names; anything but a list of integers names none."""
    episodes = said.get("episodes")
    if not isinstance(episodes, list):
        return set()
    return {e for e in episodes if isinstance(e, int) and not isinstance(e, bool)}


def ok(book, episode: int) -> bool:
    """The kind, the exact decision id, a named owner, and THIS episode listed."""
    said = read(book)
    return (said.get("kind") == "publish" and said.get("decision") == DECISION
            and bool(str(said.get("by", "")).strip()) and episode in listed(said))


def escalation(book, episode: int | None = None) -> Escalation:
    """What the owner is asked to write, and where the signature goes."""
    wanted = sorted(listed(read(book)) | ({episode} if episode is not None else set()))
    return Escalation("G-STANDING", FILE,
                      'write the standing publish approval for this book, listing every episode '
                      f'to upload: {{"kind": "publish", "decision": "{DECISION}", '
                      f'"by": "<owner>", "at": "<date>", "episodes": {wanted}}}')
