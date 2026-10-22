#!/usr/bin/env python
"""The old speech ruler beside the honest one, for every chapter of a book (craft ruling A16).

    uv run python scripts/episode/speech_ruler.py <codex> [<codex> ...]

`plan_gates.speech_share` caps a quote at 600 characters and counts a paragraph-opening thought as
speech; `plan_gates.honest_speech_share` does neither.  The dial's floor and ceiling follow the ruler,
so the switch is one line the OWNER makes after reading this table (Q1); until then the dial reads the
old ruler.  Reads `source/chapters/ch_NN.json` of each book by name (one folder).  $0, read-only.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import plan_brief, plan_gates  # noqa: E402


def chapters(book: Path) -> list[int]:
    return sorted(int(p.stem[3:]) for p in (Path(book) / "source" / "chapters").glob("ch_[0-9][0-9].json"))


def table(book: Path) -> list[tuple[int, float | None, float | None]]:
    """(chapter, old share, honest share) for every chapter of the book."""
    rows = []
    for n in chapters(book):
        paragraphs = plan_brief.chapter_paragraphs(book, n)[1]
        rows.append((n, plan_gates.speech_share(paragraphs), plan_gates.honest_speech_share(paragraphs)))
    return rows


def line(row: tuple) -> str:
    n, old, new = row
    return f"ch{n:02d}  old {old}  new {new}"


def main(argv: list[str]) -> int:
    from studio import episode_home
    for codex in argv:
        book = episode_home.book_dir(codex)
        print(book.name)
        for row in table(book):
            print("  " + line(row))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
