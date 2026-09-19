#!/usr/bin/env python
"""Rewrite refs.json's character rows for ONE chapter's cast.

    uv run python scripts/refs/cast_rows.py <book_id> <chapter> <who[=Display:gender]> ...

refs.json carries one chapter's clothes per character (`pack_refs.rows_for`);
each episode rewrites the rows of its own cast before its takes are built.
Rows outside the cast are kept as they were.  Free.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import pack_refs  # noqa: E402
from build_pack import book_dir  # noqa: E402


def parse(args: list[str]) -> tuple[list[str], dict[str, tuple[str, str]]]:
    cast, named = [], {}
    for a in args:
        who, _, rest = a.partition("=")
        cast.append(who)
        if rest:
            display, _, gender = rest.partition(":")
            named[who] = (display, gender)
    return cast, named


def main() -> None:
    book = book_dir(sys.argv[1])
    chapter = int(sys.argv[2])
    cast, named = parse(sys.argv[3:])
    path = book / "refs" / "refs.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    doc["refs"] = pack_refs.rows_for(book, chapter, cast, doc["refs"], named)
    doc["chapter"] = chapter
    path.write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
    for r in doc["refs"]:
        print(r["entity_id"], "::", r.get("display"), r.get("gender"), "::", r["physical"][-90:])


if __name__ == "__main__":
    main()
