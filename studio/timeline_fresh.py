"""Is `placed.json` still a timeline of THIS plan?

The timeline is derived: line texts and the beats and codas around them decide
every cut offset in it. Change one of those in the plan and the derived file
is no longer about the plan, but nothing downstream notices -- the take
builder simply looks for the segment holding a line's start time, finds none,
and raises `StopIteration` from inside a generator expression.

So the plan gets a fingerprint of exactly the inputs the timeline is derived
from, the timeline carries the fingerprint it was built from, and a mismatch
is a named fault with the command that cures it.
"""
from __future__ import annotations

import hashlib
import json

REBUILD = "timeline is older than the plan -- rerun scripts/episode/timeline.py"


def _inputs(episode) -> list:
    """Exactly what the timeline is derived from, in a stable order."""
    shots = sorted((s.index, s.beat_s, s.coda_s) for s in episode.shots)
    lines = sorted((l.index, l.shot, l.text) for l in episode.lines)
    return [shots, lines]


def fingerprint(episode, lines: list[dict] | None = None) -> str:
    """A hash of the timing inputs: the plan's words and holds, and -- given the
    rows of lines.json -- the MEASURED length of every line. Re-voicing a line
    changes the timeline without touching the plan, so the plan alone could
    call a stale timeline fresh (audit 2026-09-22, item 11)."""
    measured = sorted((r["index"], round(float(r["seconds"]), 3)) for r in (lines or []))
    body = json.dumps(_inputs(episode) + [measured], ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]


def stale(episode, placed: dict | None, lines: list[dict] | None = None) -> list[str]:
    """The complaint, if the timeline on disk was not built from this plan and
    this voice."""
    if not placed or placed.get("plan") != fingerprint(episode, lines):
        return [REBUILD]
    return []
