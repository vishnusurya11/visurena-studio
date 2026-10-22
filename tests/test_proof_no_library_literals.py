"""No new library path is spelled outside studio/settings.py (2026-10-21_ep02_proof 1.4).

A `/ "library"` or `Path("library")` literal in studio/ or scripts/episode|publish/ is a
path a rehearsal cannot redirect: it would read or write the real library while every other
path points at the sandbox.  The one place a library root is chosen is settings.library_root()."""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LITERAL = re.compile(r"""/\s*["']library["']|Path\(\s*["']library["']\s*\)""")
SCANNED = ("studio", "scripts/episode", "scripts/publish", "scripts/proof", "scripts/refs")
"""scripts/refs is on the episode path: step 01 runs cast_rows.py (book_dir from build_pack), step 03
imports build_pack.  Unscanned, build_pack's `parents[2] / "library"` sent the first real rehearsal's
ep02 bind to the real library ("no book matching '99991021000000'", 2026-10-21 17:45 PDT)."""
ALLOWED = {
    "studio/settings.py": "the one place a library root is chosen",
    "studio/brain.py": "_under_library DENIES a brain tool write under the repo's real library; it never "
                       "names a path to read or write, so a rehearsal has nothing to redirect there",
}


def offenders() -> list[str]:
    """`file:line: text` for every library literal in the scanned code outside ALLOWED."""
    found = []
    for top in SCANNED:
        for path in sorted((REPO / top).rglob("*.py")):
            rel = path.relative_to(REPO).as_posix()
            if rel in ALLOWED:
                continue
            for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if LITERAL.search(line):
                    found.append(f"{rel}:{n}: {line.strip()}")
    return found


def test_no_library_literal_outside_settings():
    assert offenders() == []


def test_the_pattern_catches_both_spellings():
    assert LITERAL.search('LIB = ROOT / "library"') and LITERAL.search("P = Path('library') / 'x'")
    assert not LITERAL.search('icon("library")') and not LITERAL.search("settings.library_root()")
