"""Which book a file belongs to, found rather than counted to.

`storyboard.book_of` was `Path(out).resolve().parents[3]`, with the docstring
"the book folder above `episodes/epNN/frames/<file>`".  That is a hard-coded
DEPTH: correct for exactly one layout, and silently wrong for every other.

MEASURED 2026-09-13, the hour the sheets moved from `frames/` into
`boards/sheets/`: seven paid gpt-image calls -- $0.91 of real money -- were
recorded into `library/<book>/episodes/spend.jsonl` instead of
`library/<book>/spend.jsonl`.  Nothing raised, nothing printed, and the episode
read as having cost $0.08.

A ledger that can be written to the wrong file without anyone noticing is worse
than no ledger, because it is read as complete.  So a book is identified by what
a book HAS, and a path that belongs to no book is an error rather than a guess.
"""
from __future__ import annotations

from pathlib import Path

MARKS = ("refs", "episodes")
"""What every book has and nothing inside one has at the same time."""


def is_book(path: Path) -> bool:
    return all((path / mark).is_dir() for mark in MARKS)


def of(path: Path) -> Path:
    """The book folder this file lives under, at any depth.

    The NEAREST book wins, so a stray `refs/` deeper in the tree cannot capture
    a file that belongs to the book above it."""
    here = Path(path).resolve()
    for folder in here.parents:
        if is_book(folder):
            return folder
    raise FileNotFoundError(f"no book above {path}: a book has {' and '.join(MARKS)}/")
