"""A tiny rehearsal sandbox built from tests/fixtures only (DESIGN 2026-10-21_ep02_proof 1.3).

No test reads the HDD library: the "real" book and the "real" DB here are made in a tmp
folder from small fixture files, then `studio.rehearsal.sandbox.build` runs on them exactly
as it runs on the Jekyll book.  `stand_in_roots` gives the folders a fence test treats as
the real roots, so a planted write can be refused without ever touching library/."""
from __future__ import annotations

import shutil
import sqlite3
from contextlib import closing
from pathlib import Path

from studio.rehearsal import sandbox

FIXTURES = Path(__file__).resolve().parent / "fixtures"
RECORDS = {"analysis/scenes.json": "scarlet_scenes.json", "refs/pins.json": "gate_pins.json",
           "source/lines.json": "trailer_lines.json"}
"""Book-relative record -> the fixture file that stands in for it."""


def real_book(root: Path) -> Path:
    """A stand-in for the real Jekyll book: three named records copied from tests/fixtures."""
    book = root / "real_library" / f"{sandbox.REAL_CODEX}_{sandbox.SLUG}"
    for rel, fixture in RECORDS.items():
        (book / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(FIXTURES / fixture, book / rel)
    return book


def real_db(root: Path) -> Path:
    """A stand-in for db/visurena_studio.db holding the real codex row."""
    from studio import db
    path = root / "real_db" / "visurena_studio.db"
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(db.get_connection(path)) as conn:
        db.init_db(conn)
        conn.execute("INSERT OR IGNORE INTO codex (id, name, source_type, updated_at) VALUES (?, ?, 'gutenberg', ?)",
                     (sandbox.REAL_CODEX, "The Strange Case of Dr Jekyll and Mr Hyde", "2026-08-27T13:55:04Z"))
        conn.commit()
    return path


def tiny_sandbox(root: Path, run_id: str = "t1", **manifest) -> Path:
    """Build a sandbox under `root` from the stand-ins; returns the sandbox folder."""
    book, base = real_book(root), root / "rehearsals"
    fields = {"fakes": False, "real_library": str(book.parent), **manifest}
    return sandbox.build(run_id, source_book=book, real_db=real_db(root), base=base,
                         records=tuple(sorted({r.split("/")[0] for r in RECORDS})), manifest=fields)


def stand_in_roots(root: Path) -> tuple[Path, Path]:
    """(real library, real db folder) of the stand-ins, for a fence armed in a test."""
    return root / "real_library", root / "real_db"


def codex_ids(db_path: Path) -> list[str]:
    with closing(sqlite3.connect(db_path)) as conn:
        return [r[0] for r in conn.execute("SELECT id FROM codex ORDER BY id")]


def env_for(box: Path) -> dict[str, str]:
    """The one variable a rehearsal process carries."""
    return {"VISURENA_LIBRARY": str(box / "library")}
