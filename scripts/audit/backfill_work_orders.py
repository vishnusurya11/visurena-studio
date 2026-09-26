#!/usr/bin/env python
"""The Command Center's backfill (decision 2026-09-25, "Migration, zero loss"):
the work-order rows the library's files imply, listed first, written only on
the owner's word.

    uv run python scripts/audit/backfill_work_orders.py [--book <codex>] [--write] [--force] [--with-publish]

The default is a DRY RUN: the DB is opened read-only and the listing printed
(one line per unit -- derived state, step, verdict words, flags, GPU hours,
and why the row would not be written).  `--write` upserts the unambiguous
rows with source='backfill', never a row whose run is live; `--force` writes
the ambiguous ones too; `--with-publish` adds the publish rows from
youtube.json + uploads.jsonl although the registry has no `publish` stage
yet.  The logic is studio.backfill; this is the door.
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import backfill, db, episode_home  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]


def open_readonly(path: Path) -> sqlite3.Connection:
    """The DB as a reader: a live run owns it, and a dry run writes nothing."""
    conn = sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def open_writable(path: Path) -> sqlite3.Connection:
    """The DB as a writer, migrated (CREATE IF NOT EXISTS / ADD COLUMN only)."""
    conn = db.get_connection(path)
    db.init_db(conn)
    return conn


def options(argv: list[str]) -> dict:
    """--book <codex> | --book=<codex> (a folder name is cut to its id), and the three flags."""
    books = []
    for i, arg in enumerate(argv[1:], 1):
        if arg.startswith("--book="):
            books.append(arg.split("=", 1)[1][:14])
        elif arg == "--book" and i + 1 < len(argv):
            books.append(argv[i + 1][:14])
    return {"books": books or None, "write": "--write" in argv, "force": "--force" in argv,
            "with_publish": "--with-publish" in argv}


def main(argv: list[str], conn: sqlite3.Connection | None = None, library: Path | None = None) -> int:
    opts = options(argv)
    if conn is None:
        conn = open_writable(ROOT / db.DB_PATH) if opts["write"] else open_readonly(ROOT / db.DB_PATH)
    entries = backfill.plan(conn, library or episode_home.LIBRARY, opts["books"],
                            with_publish=opts["with_publish"])
    print(backfill.listing(entries))
    if opts["write"]:
        print(f"wrote {backfill.write(conn, entries, force=opts['force'])} rows")
    else:
        print("dry run: nothing written (--write to upsert; --force for the ambiguous rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
