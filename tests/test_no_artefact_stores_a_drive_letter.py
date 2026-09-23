"""No artefact in the library stores an absolute path.

CLAUDE.md: never store an absolute path -- production_id plus a relative path
only. Audit item 15, measured 2026-09-22: 291 take reports stored `strip` as
an absolute path into the worktree, and two voice reports stored `clip` the
same way. A path with a drive letter breaks the moment the library moves.

The pattern requires the drive letter to open a JSON string ("D:\\...") -- a
bare `:\\` also matches the escaped newline in "definitions:\\n", which is how
a first count of this came out at 537 files.
"""
import re
from pathlib import Path

import pytest

BOOK = Path(__file__).resolve().parents[1] / "library" / "20260827135508_the-war-of-the-worlds"
DRIVE = re.compile(r'"[A-Za-z]:(?:\\\\|/)')


@pytest.mark.skipif(not BOOK.exists(), reason="no library on this machine")
def test_no_json_artefact_in_the_book_stores_a_drive_letter():
    hits = [p.relative_to(BOOK).as_posix() for p in BOOK.rglob("*")
            if p.is_file() and p.suffix in (".json", ".jsonl")
            and DRIVE.search(p.read_text(encoding="utf-8", errors="ignore"))]
    assert not hits, f"{len(hits)} artefacts store an absolute path, e.g. {hits[:5]}"
