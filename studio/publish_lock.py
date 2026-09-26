"""The publish lock: every reason a master may not reach the platform.

ROOT CAUSE 2026-09-26 (docs/audit/2026-09-26_ep12_root_cause.md).  Episode 12
went public with every taste gate ended in a TERMINAL -- PLAN and EYE_PANELS
kept-best (the panels at attempt 0, never judged), EYE_TAKES kept-best, MASTER
flagged -- and with the narrator's voice check `ok: false`.  Nothing between
the runner and the channel read any of it.  So the upload and the privacy flip
both ask this module, and it answers from the unit's own files:

    learnings.jsonl          the last row per gate; a terminal is a stop
    review/waiver.json       {gate: reason} -- the OWNER's hand only
    review/speaker_check.json  a speaker that is not one voice is a stop
    review/director_signoff.md  watched, strips read, coverage, flags -- per cut
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from studio.learnings import Learning, load

SECTIONS = ("Watched", "Take strips", "Coverage", "Flags")
"""What the director writes before a stranger sees the cut: the master watched
full size WITH sound, every take strip read, the plan's last paragraph against
the chapter's, and every open flag accepted or refused."""
MIN_SECTION = 8
"""Characters a section needs to count as written, not left as a heading."""


def last_by_gate(rows: list[Learning]) -> dict[str, Learning]:
    """The latest row per gate; budget rows are the climb's bookkeeping, not a gate."""
    return {r.gate: r for r in rows if r.gate != "budget"}


def open_terminals(home: Path) -> list[str]:
    """Every gate whose latest row ended in a terminal (keep_best, flag, still ...)."""
    path = Path(home) / "learnings.jsonl"
    rows = last_by_gate(load(path)) if path.exists() else {}
    return [f"{gate} ended {r.action}" + (f": {r.note[:160]}" if r.note else "")
            for gate, r in rows.items() if r.terminal]


def waivers(home: Path) -> dict[str, str]:
    """{gate: reason} the owner wrote; a blank reason waives nothing."""
    path = Path(home) / "review" / "waiver.json"
    doc = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    return {k: str(v).strip() for k, v in doc.items() if str(v).strip()}


def speaker_stops(home: Path) -> list[str]:
    """A speaker the voice check found is not one voice across the episode."""
    path = Path(home) / "review" / "speaker_check.json"
    doc = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    return [f"speaker_check: {who} is not one voice (worst pair {float(row.get('worst', 0)):.3f})"
            for who, row in doc.items() if isinstance(row, dict) and row.get("ok") is False]


def sections(text: str) -> dict[str, str]:
    """`## Heading` -> the text under it, stripped."""
    parts = re.split(r"^##\s+(.+?)\s*$", text, flags=re.M)
    return {parts[i].strip(): parts[i + 1].strip() for i in range(1, len(parts) - 1, 2)}


def signoff_stops(home: Path, sha8: str) -> list[str]:
    """The director's sign-off exists, names THIS cut, and every section is written."""
    path = Path(home) / "review" / "director_signoff.md"
    if not path.exists():
        return ["director_signoff.md is missing: watch, listen and sign before publishing"]
    text = path.read_text(encoding="utf-8")
    if sha8 not in text:
        return [f"director_signoff.md does not name this cut ({sha8})"]
    got = sections(text)
    return [f"director_signoff.md section '{name}' is empty" for name in SECTIONS
            if len(got.get(name, "")) < MIN_SECTION]


def stops(home: Path, sha8: str) -> list[str]:
    """Every reason this cut may not be published, owner waivers applied."""
    waived = waivers(home)
    held = [t for t in open_terminals(home) if t.split(" ", 1)[0] not in waived]
    voice = [] if "speaker_check" in waived else speaker_stops(home)
    return held + voice + signoff_stops(home, sha8)
