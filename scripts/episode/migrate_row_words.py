#!/usr/bin/env python
"""The one-time row-word migration: every stillness word already filed in
refs.json physicals and analysis/props cards, cured by the shared table.

    uv run python scripts/episode/migrate_row_words.py <codex_id> [--write]

Dry by default: prints every field's before/after and writes NOTHING without
--write.  Ongoing protection is G-ROWTEXT at `pack_refs.rows_for` (the
bind-time wall), so this migration never needs a second run -- and a second
run reports nothing, because the table is idempotent.  The refs.json write
goes through its whole-document path, so a verdict keyed on its bytes lapses
honestly."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import episode_home, row_lint  # noqa: E402


def refs_fixes(book: Path) -> list[tuple[str, str, str]]:
    """(label, before, after) for every character physical the table cures."""
    path = book / "refs" / "refs.json"
    rows = (episode_home.read_json(path).get("refs") or []) if path.exists() else []
    out = []
    for r in rows:
        said = r.get("physical") or ""
        cured = row_lint.cure_row_text(said)
        if r.get("kind") == "character" and said and cured != said:
            out.append((f"row {r.get('entity_id')} physical", said, cured))
    return out


def prop_fixes(book: Path) -> list[tuple[str, str, str]]:
    """(label, before, after) for every props-card profile field the table cures."""
    folder = book / "analysis" / "props"
    out = []
    for path in sorted(folder.glob("*.json")) if folder.exists() else []:
        if path.stem == "index":
            continue
        prof = (episode_home.read_json(path).get("profile") or {})
        for key in ("physical", "scale"):
            said = prof.get(key) or ""
            cured = row_lint.cure_row_text(said)
            if said and cured != said:
                out.append((f"card {path.stem} {key}", said, cured))
    return out


def write_fixes(book: Path, fixes: list[tuple[str, str, str]]) -> int:
    """Each cured field written back through studio.row_lint's own writers."""
    wrote = 0
    for label, _, _ in fixes:
        layer, ident = label.split()[0], label.split()[1]
        wrote += bool(row_lint.cure_row_file(book, layer, ident))
    return wrote


def migrate(book: Path, write: bool = False) -> list[tuple[str, str, str]]:
    """The whole migration, dry unless `write`: the fixes found (and printed)."""
    fixes = refs_fixes(book) + prop_fixes(book)
    for label, before, after in fixes:
        print(f"{label}:\n  - {before[:160]}\n  + {after[:160]}")
    if not fixes:
        print("nothing to cure: every row and card is clean under the table")
    elif write:
        print(f"{write_fixes(book, fixes)} file(s) rewritten")
    else:
        print(f"DRY RUN: {len(fixes)} field(s) would change; pass --write to apply")
    return fixes


if __name__ == "__main__":
    migrate(episode_home.book_dir(sys.argv[1]), "--write" in sys.argv)
