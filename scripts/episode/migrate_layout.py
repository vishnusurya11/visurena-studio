#!/usr/bin/env python
"""Move an episode from the flat folders into the named rooms.  Idempotent.

    uv run python scripts/episode/migrate_layout.py <codex_id> <episode> [--dry-run]

WHAT MOVES, and why each file knows where it belongs:

    lines/                   -> audio/lines/
    frames/plate_*.png       -> boards/plates/
    frames/seq_*             -> boards/sheets/     (the sheets, prompts and dq)
    frames/Q*.png            -> boards/cells/      (minus the drafts below)
    frames/*.before.png      -> boards/panels/     a superseded draft is not a cell
    frames/panel_*           -> boards/panels/
    shots_<engine>/T*_fail*  -> takes/<engine>/attempts/
    shots_<engine>/          -> takes/<engine>/
    work_<engine>/           -> takes/work/
    master*.mp4              -> cut/
    qc*.json, *.html         -> reports/

Nothing is renamed: a file keeps the name it has, so every prompt, record and
report that names it still reads true.  Only the room changes.

A file already in its room is left alone, so this can be run twice, and a file
that exists in BOTH places is a conflict the script refuses rather than
resolving -- silently choosing between two copies of a picture is exactly the
class of fault this layout exists to prevent.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from studio import episode_home


def room_for(path: Path, home: Path) -> Path | None:
    """The folder this file belongs in now, or None to leave it where it is."""
    name, parent = path.name, path.parent.name
    if parent == "lines":
        return home / "audio" / "lines"
    if parent == "frames":
        if ".before." in name or name.startswith("panel_"):
            return home / "boards" / "panels"
        if name.startswith("plate_"):
            return home / "boards" / "plates"
        if name.startswith("seq_"):
            return home / "boards" / "sheets"
        if name.startswith(("Q", "S", "C")):
            return home / "boards" / "cells"
        if name.endswith(".json"):
            return home / "reports"
        return home / "boards"
    if parent.startswith("shots"):
        engine = parent.split("_", 1)[1] if "_" in parent else "i2v"
        if "_fail" in name:
            return home / "takes" / engine / "attempts"
        return home / "takes" / engine
    # a work dir nests (`work_r2v/dq/`), so the whole path is asked, not just
    # the immediate parent
    if any(part.startswith("work_") or part == "work" for part in path.parts[:-1]):
        keep = path.parent.name if path.parent.name not in ("work", ) and not path.parent.name.startswith("work_") else ""
        return home / "takes" / "work" / keep if keep else home / "takes" / "work"
    if any(part == "frames_superseded" for part in path.parts[:-1]):
        return home / "boards" / "panels"
    if path.parent == home:
        if name.startswith("master") and name.endswith(".mp4"):
            return home / "cut"
        if name.startswith("qc") and name.endswith(".json"):
            return home / "reports"
        if name.endswith(".html") or name == "sheet_dq.json":
            return home / "reports"
    return None


def moves(home: Path) -> list[tuple[Path, Path]]:
    """Every file that is not yet in its room, with where it goes."""
    out = []
    for path in sorted(home.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        room = room_for(path, home)
        if room is None or path.parent == room:
            continue
        out.append((path, room / path.name))
    return out


def repoint(book: Path, home: Path, plan: list[tuple[Path, Path]]) -> None:
    """Rewrite every book-relative path a record holds for a file that moved.

    A record that names a file by its OLD room is not a broken string, it is a
    silent false green: `edit_gate` reads `rel_path`, finds nothing, and reports
    `measured: False` -- which the ladder has been reading as a pass.  Migrating
    the pictures without migrating the records would hand every episode an
    unmeasurable provenance check.
    """
    moved = {episode_home.relative(book, src): episode_home.relative(book, dest)
             for src, dest in plan}
    if not moved:
        return
    touched = 0
    for record in sorted(home.rglob("*.json")):
        text = was = record.read_text(encoding="utf-8")
        for old, new in moved.items():
            if old in text:
                text = text.replace(old, new)
        if text != was:
            record.write_text(text, encoding="utf-8")
            touched += 1
            print(f"  repointed {record.relative_to(home).as_posix()}")
    if touched:
        print(f"  {touched} record(s) now name the files where they are")


def main(book_id: str, number: int, dry: bool) -> None:
    book = episode_home.book_dir(book_id)
    home = episode_home.home(book, number)
    if not home.exists():
        raise SystemExit(f"no episode at {home}")
    plan = moves(home)
    clashes = [(a, b) for a, b in plan if b.exists()]
    if clashes:
        raise SystemExit("two copies of the same file; refusing to choose:\n  "
                         + "\n  ".join(f"{a.name}: {a} and {b}" for a, b in clashes))
    for src, dest in plan:
        print(f"  {src.relative_to(home).as_posix():46} -> {dest.relative_to(home).as_posix()}")
        if not dry:
            dest.parent.mkdir(parents=True, exist_ok=True)
            src.replace(dest)
    if not dry:
        repoint(book, home, plan)
        for stale in sorted((p for p in home.rglob("*") if p.is_dir()), reverse=True):
            if not any(stale.iterdir()):
                stale.rmdir()
    print(f"\n{len(plan)} file(s){' would move' if dry else ' moved'}\n{home}")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    main(args[0], int(args[1]), "--dry-run" in sys.argv)
