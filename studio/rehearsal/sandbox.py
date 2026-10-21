"""Build a rehearsal sandbox on C: and checkpoint it at step boundaries (2026-10-21_ep02_proof 1.3).

<sandbox> = %LOCALAPPDATA%\\Temp\\visurena_rehearsal\\<run_id>\\ holds the sandbox book (its own
codex 99991021000000, copied from NAMED records of the real book, never a walk of library/),
the sandbox DB (the real codex row copied by SELECT, renumbered, plus the episode's queue
row), the fake engine's comfy/ dirs, a 1-commit git repo, tmp/ and rehearsal.json.  The
book's records are copied off the HDD ONCE into a golden copy and reused by every build.
A checkpoint is a folder copy of library/, db/, comfy/ and git/; a restore puts it back and
the real resume code runs from there.  The builder runs outside rehearsal mode (unfenced): it
is the one reader of the real DB, opened read-only."""
from __future__ import annotations

import json
import os
import shutil
import sqlite3
import stat
import subprocess
from contextlib import closing
from pathlib import Path
from typing import Iterable, Mapping

from studio import settings

SANDBOX_CODEX = "99991021000000"
REAL_CODEX = "20260827135504"
SLUG = "the-strange-case-of-dr-jekyll-and-mr-hyde"
BOOK_RECORDS = ("analysis", "cast", "refs", "source", "title")
"""The real book's top-level records an episode reads (stages.yaml `in:` globs); named, never globbed."""
CHECKPOINTED = ("library", "db", "comfy", "git")
DIRS = ("library/.autopilot", "library/.device", "library/.vlm_cache", "comfy/input", "comfy/output",
        "comfy/temp", "tmp", "db")
DEFAULT_HOST = "http://127.0.0.1:18188"
GOLDEN_MARK = ".golden.json"


def default_base() -> Path:
    """%LOCALAPPDATA%\\Temp\\visurena_rehearsal: the NVMe, never the D: spinning disk."""
    return Path(os.environ["LOCALAPPDATA"]) / "Temp" / "visurena_rehearsal"


def book_name(codex: str = SANDBOX_CODEX) -> str:
    return f"{codex}_{SLUG}"


def copy_records(src_book: Path, dest: Path, records: Iterable[str]) -> list[str]:
    """Copy each named top-level record (file or folder) that exists; the names copied."""
    copied = []
    for name in records:
        src = Path(src_book) / name
        if src.is_dir():
            shutil.copytree(src, dest / name)
        elif src.is_file():
            dest.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest / name)
        else:
            continue
        copied.append(name)
    return copied


def golden(src_book: Path, base: Path, records: tuple[str, ...]) -> Path:
    """The book's golden copy under <base>/golden, made from the HDD once per record set."""
    dest = base / "golden" / book_name()
    mark = dest / GOLDEN_MARK
    if mark.is_file() and json.loads(mark.read_text(encoding="utf-8")).get("records") == list(records):
        return dest
    if dest.exists():
        shutil.rmtree(dest, onexc=_writable)
    building = dest.with_name(dest.name + ".building")
    if building.exists():
        shutil.rmtree(building, onexc=_writable)
    copied = copy_records(src_book, building, records)
    building.mkdir(parents=True, exist_ok=True)
    (building / GOLDEN_MARK).write_text(json.dumps({"records": list(records), "copied": copied,
                                                    "source": str(src_book)}), encoding="utf-8")
    building.rename(dest)
    return dest


def codex_row(real_db: Path, codex: str) -> dict:
    """The real codex row, read through a read-only URI (the real DB is never opened writable)."""
    uri = f"file:{Path(real_db).resolve().as_posix()}?mode=ro"
    with closing(sqlite3.connect(uri, uri=True)) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM codex WHERE id = ?", (codex,)).fetchone()
    if row is None:
        raise LookupError(f"codex {codex} is not in {real_db}")
    return dict(row)


def make_db(path: Path, row: Mapping, episode: int) -> Path:
    """The sandbox DB: the schema, the codex row renumbered to the sandbox id, the queue row."""
    from studio import db
    with closing(db.get_connection(path)) as conn:
        db.init_db(conn)
        have = [r[1] for r in conn.execute("PRAGMA table_info(codex)")]
        fields = {k: v for k, v in {**row, "id": SANDBOX_CODEX}.items() if k in have}
        conn.execute(f"INSERT INTO codex ({', '.join(fields)}) VALUES ({', '.join('?' * len(fields))})",
                     tuple(fields.values()))
        conn.commit()
        db.upsert_work_order(conn, SANDBOX_CODEX, "episode", f"ep{episode:02d}", number=episode, state="queued")
    return path


def make_git(folder: Path) -> Path:
    """A 1-commit repo that answers HEAD and a clean porcelain, and nothing of the real tree."""
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "README").write_text("rehearsal sandbox: HEAD and porcelain only\n", encoding="utf-8")
    ident = ["-c", "user.name=rehearsal", "-c", "user.email=rehearsal@localhost", "-c", "commit.gpgsign=false"]
    for argv in (["init", "-q"], ["add", "README"], [*ident, "commit", "-q", "-m", "rehearsal sandbox"]):
        subprocess.run(["git", *argv], cwd=folder, check=True, capture_output=True, text=True)
    return folder


def write_manifest(box: Path, run_id: str, episode: int, fields: Mapping) -> dict:
    manifest = {"run_id": run_id, "codex": SANDBOX_CODEX, "episode": episode, "comfy_host": DEFAULT_HOST,
                "recordings": None, "real_library": str(settings.REAL_LIBRARY),
                "real_roots": [], "scale": 1, "faults": [], "fakes": True, **fields}
    (box / "rehearsal.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    return manifest


def build(run_id: str, *, source_book: Path, real_db: Path, base: Path | None = None, episode: int = 2,
          records: tuple[str, ...] = BOOK_RECORDS, manifest: Mapping | None = None) -> Path:
    """<base>/<run_id>: a new sandbox for one rehearsal run (a run id is never reused)."""
    base = Path(base or default_base())
    box = base / run_id
    if box.exists():
        raise FileExistsError(f"sandbox {box} exists: a run id is built once")
    book = golden(source_book, base, records)
    for rel in DIRS:
        (box / rel).mkdir(parents=True, exist_ok=True)
    shutil.copytree(book, box / settings.LIBRARY_DIR / book_name(), ignore=shutil.ignore_patterns(GOLDEN_MARK))
    make_db(box / "db" / "visurena_studio.db", codex_row(real_db, REAL_CODEX), episode)
    make_git(box / "git")
    write_manifest(box, run_id, episode, manifest or {})
    return box


def _writable(func, path, _exc) -> None:
    """rmtree's retry for git's read-only object files on Windows."""
    os.chmod(path, stat.S_IWRITE)
    func(path)


def checkpoint(box: Path, name: str) -> Path:
    """Copy library/, db/, comfy/ and git/ to <sandbox>/checkpoints/<name> (replacing one of that name)."""
    dest = box / "checkpoints" / name
    if dest.exists():
        shutil.rmtree(dest, onexc=_writable)
    for top in CHECKPOINTED:
        shutil.copytree(box / top, dest / top)
    return dest


def restore(box: Path, name: str) -> None:
    """Put a checkpoint's folders back exactly: what was added since is gone, what changed is undone."""
    src = box / "checkpoints" / name
    if not src.is_dir():
        raise FileNotFoundError(f"no checkpoint {name} in {box}")
    for top in CHECKPOINTED:
        shutil.rmtree(box / top, onexc=_writable)
        shutil.copytree(src / top, box / top)
