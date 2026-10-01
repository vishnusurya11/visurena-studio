#!/usr/bin/env python
"""Pre-bake a book's title cards in ONE session, before any episode runs.

    uv run python scripts/episode/titles_batch.py <codex_id>              # every chapter missing a card
    uv run python scripts/episode/titles_batch.py <codex_id> <first> <last>

THE DESIGN (owner, 2026-09-30): a book's cards all exist BEFORE its first
episode starts; an episode never renders a card mid-run.  The card cost
17-25 min inside every episode's window (ep14 rendered it twice) on a second
H3 model, yet it depends only on the book, the chapter title and the series
aspect.  One process renders the set back to back, so the i2v model loads
once; a card already on disk is skipped (series_title.main's own rule), making
the run resumable and idempotent.  drive.py calls `missing()` before every
launch and bakes the stragglers first."""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.episode import series_title  # noqa: E402
from studio import episode_home  # noqa: E402


def chapters_of(book: Path) -> list[int]:
    """The book's chapter numbers with a source file, 1 up (ch_00 is front matter)."""
    out = []
    for p in sorted((Path(book) / "source" / "chapters").glob("ch_*.json")):
        if (m := re.fullmatch(r"ch_(\d+)", p.stem)) and int(m.group(1)) > 0:
            out.append(int(m.group(1)))
    return out


def missing(book: Path) -> list[int]:
    """The chapters whose animated card is not on disk yet."""
    return [n for n in chapters_of(book) if not (Path(book) / "title" / f"ep{n:02d}.mp4").exists()]


def numbers_of(argv: list[str]) -> list[int]:
    """<first> <last> inclusive; a single number is itself; nothing means
    'every chapter missing a card' (resolved in main)."""
    plain = [int(a) for a in argv if a.isdigit()]
    if not plain:
        return []
    first, last = plain[0], plain[-1]
    if last < first:
        raise SystemExit(f"last ({last}) is before first ({first})")
    return list(range(first, last + 1))


def main(book_id: str, numbers: list[int]) -> int:
    if not numbers:
        numbers = missing(episode_home.book_dir(book_id))
        if not numbers:
            print("every chapter's card is on disk; nothing to bake")
            return 0
    for n in numbers:
        print(f"ep{n:02d}:", flush=True)
        series_title.main(book_id, n)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], numbers_of(sys.argv[2:])))
