#!/usr/bin/env python
"""Land the book's authored heads (analysis/heads.json) in its dossiers.

    uv run python scripts/refs/author_heads.py <book_id>

Run before `looks_table.py` when the profile writer found no hair, beard or hat
for a bound character (the look table refuses it "head unauthored").  Every
quote is checked against its chapter, every head must name hair, facial hair
and a hat, and no two bound characters may share a face; else nothing is
written (`studio.head_author`).  Free: no model call.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.refs import looks_table  # noqa: E402
from studio import episode_home, head_author  # noqa: E402


def main(book_id: str) -> int:
    book = episode_home.book_dir(book_id)
    for who in head_author.apply(book, looks_table.rows(book)):
        print(f"  head: {who}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
