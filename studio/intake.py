"""Register a book: a codex row, a library folder, and its EPUB in place.

Doing this by hand once was fine. Doing it ten times by hand is how the folders drift,
and the layout is load-bearing: `paths.book_dir` finds a book by globbing `<id>_*` and
RAISES unless exactly one folder matches, while step 03 reads `source/chapters/`.
"""

from __future__ import annotations

import re
import shutil
import sqlite3
from pathlib import Path

from studio import db, paths

MAX_SLUG = 60
_KEEP = re.compile(r"[^a-z0-9]+")

# Every stage's output lives under the book, so the folder is made once, here.
SUBFOLDERS = ("source", "analysis", "screenplay", "audiobook", "video", "publish")


def slug(name: str) -> str:
    """Lowercase, hyphenated, punctuation dropped. Cosmetic — the id is the anchor."""
    text = _KEEP.sub("-", (name or "").lower()).strip("-")
    if len(text) <= MAX_SLUG:
        return text
    return text[:MAX_SLUG].rsplit("-", 1)[0]


def register(conn: sqlite3.Connection, name: str, *, source_ref: str,
             epub: Path | None = None, library_root: Path | None = None,
             **fields) -> str:
    """Create the codex row and the folder. Returns the codex id.

    Refuses a duplicate rather than making a second folder: two folders for one book
    make `paths.book_dir` ambiguous, and it raises on anything but exactly one match.
    """
    root = Path(library_root or paths.LIBRARY_ROOT)
    existing = conn.execute(
        "SELECT id FROM codex WHERE source_ref = ?", (source_ref,)).fetchone()
    if existing:
        raise ValueError(f"{source_ref} is already registered as {existing['id']}")

    codex_id = db.insert_codex(conn, name, source_type="gutenberg",
                               source_ref=source_ref, **fields)
    folder = root / f"{codex_id}_{slug(name)}"
    for sub in SUBFOLDERS:
        (folder / sub).mkdir(parents=True, exist_ok=True)
    if epub:
        shutil.copy2(epub, folder / "source" / Path(epub).name)
    return codex_id
