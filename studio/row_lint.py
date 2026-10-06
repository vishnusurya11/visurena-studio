"""The row-text lint and its substitution table, shared by every data layer.

A cast row's `physical` and a prop card's `profile` text are injected VERBATIM
into every take prompt that stages them (`episode_ref_official.subjects` and
the prop definitions), so one stillness word in a row poisons every take of
the episode.  This module lints and cures that text where it is WRITTEN -- the
bind-time wall in `pack_refs.rows_for`, the one-time migration CLI, and the
`[row <id>]`/`[card <pid>]` cure dispatch -- with the same ordered table the
plan-layer cure (`plan_cures.stillness_words`) imports, so plan and row layers
can never drift apart on what a stillness word becomes.

Pure text in, text out; no book names anywhere.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from studio import episode_ref_official as ro

TABLE: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\bholds her fire\b", re.I), "her guns silent"),
    (re.compile(r"\bheld at\b", re.I), "resting at"),
    (re.compile(r"\bheld in\b", re.I), "clutched in"),
    (re.compile(r"\bholds?\b(?! a static shot)"
                r"(?=\s+(?:the|a|an|his|her|its|their|both|one|two)\b)", re.I), "grips"),
    (re.compile(r"\bheld\b", re.I), "clutched"),
    (re.compile(r"\b(?:remains?|stays?)\b", re.I), "keeps"),
    (re.compile(r"\bwaits?\b", re.I), "stands ready"),
]
"""Ordered, most specific first; a word the table misses stays in the text and
falls to the llm cure.  A bare `holds` with no object after it is one of those:
`grips` needs a thing to grip, so the swap fires only when one follows."""

AT_REST_TABLE: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\b(?:motionless|frozen|unmoving)\b", re.I), "at rest"),
]
"""Legal only where the stillness IS the picture asked for: the `at_rest`
field.  Anywhere else these words are the llm cure's."""


def substituted(text: str, at_rest: bool = False) -> str:
    """The shared table over one text; `at_rest` admits the at-rest swaps."""
    out = text or ""
    for pattern, said in TABLE + (AT_REST_TABLE if at_rest else []):
        out = pattern.sub(said, out)
    return out


def cure_row_text(text: str) -> str:
    """One row text cured: the table, then the pace append on a person's gait
    (`ro.paced` is idempotent, so so is this)."""
    return ro.paced(substituted(text))


def row_faults(text: str) -> list[str]:
    """Why this row text would fail the take lint, in the lint's own words:
    its STILL regex, an unpaced person gait, `slow`, and negations."""
    body = ro.scrub(text or "")
    out = []
    if bad := sorted({m.group(0).lower()
                      for m in ro.STILL.finditer(body.replace("holds a static shot", " "))}):
        out.append(f"L2 STILLNESS: {bad}")
    if ro.gaits(body) and not any(p in body.lower() for p in ro.PACE):
        out.append("L8 NO PACE: a walk, climb or ride with no pace named")
    if ro.SLOW.search(body):
        out.append("L3 SLOW: the limp carries the slowness, never the word")
    if bad := ro.negations(body):
        out.append(f"L1 NEGATION: {bad}")
    return out


def _refs_path(book: Path) -> Path:
    return Path(book) / "refs" / "refs.json"


def _card_path(book: Path, pid: str) -> Path:
    return Path(book) / "analysis" / "props" / f"{pid}.json"


def read_row_text(book: Path, layer: str, ident: str) -> str | None:
    """The text a `[row <id>]` or `[card <pid>]` fault points at, or None."""
    if layer == "row":
        doc = json.loads(_refs_path(book).read_text(encoding="utf-8"))
        row = next((r for r in doc.get("refs") or [] if r.get("entity_id") == ident), None)
        return (row or {}).get("physical")
    path = _card_path(book, ident)
    if not path.exists():
        return None
    prof = json.loads(path.read_text(encoding="utf-8")).get("profile") or {}
    return prof.get("physical")


def write_row_text(book: Path, layer: str, ident: str, text: str) -> bool:
    """One verified rewrite written to its own layer's file; False when the
    target row or card is not there to take it."""
    if layer == "row":
        return _write_refs_physical(book, ident, lambda _: text)
    return _write_card_profile(book, ident, {"physical": text})


def cure_row_file(book: Path, layer: str, ident: str) -> bool:
    """The mechanical table over one row's or card's own file; True when the
    file changed.  The refs write goes through the whole-document path, so a
    refs verdict keyed on its bytes lapses honestly."""
    if layer == "row":
        return _write_refs_physical(book, ident, cure_row_text)
    path = _card_path(book, ident)
    if not path.exists():
        return False
    prof = json.loads(path.read_text(encoding="utf-8")).get("profile") or {}
    cured = {k: cure_row_text(prof[k]) for k in ("physical", "scale")
             if prof.get(k) and cure_row_text(prof[k]) != prof[k]}
    return _write_card_profile(book, ident, cured) if cured else False


def _write_refs_physical(book: Path, ident: str, rewrite) -> bool:
    """refs.json with one character row's physical rewritten; False untouched."""
    from studio import episode_home
    path = _refs_path(book)
    if not path.exists():
        return False
    doc = episode_home.read_json(path)
    row = next((r for r in doc.get("refs") or [] if r.get("entity_id") == ident), None)
    if row is None or not row.get("physical"):
        return False
    said = rewrite(row["physical"])
    if said == row["physical"]:
        return False
    row["physical"] = said
    episode_home.write_json(path, doc)
    return True


def _write_card_profile(book: Path, pid: str, fields: dict[str, str]) -> bool:
    """analysis/props/<pid>.json with profile fields replaced; False untouched."""
    from studio import episode_home
    path = _card_path(book, pid)
    if not path.exists() or not fields:
        return False
    card = episode_home.read_json(path)
    prof = card.setdefault("profile", {})
    prof.update(fields)
    episode_home.write_json(path, card)
    return True
