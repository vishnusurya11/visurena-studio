"""The `/lib/{codex}/{path}` guard (report D §3): a book's artefacts and
nothing else.  The codex is 14 digits, the folder is the one that starts with
it, the resolved path must stay under that folder (so `..` and a symlink out
both fail), the suffix must be on the allowlist and the target must be a file.
Every refusal is None; the route turns it into a 404, never a 403."""
from __future__ import annotations

import re
from pathlib import Path, PurePosixPath

CODEX = re.compile(r"^\d{14}$")
SUFFIXES = frozenset({".png", ".jpg", ".jpeg", ".mp4", ".wav", ".json", ".jsonl", ".txt", ".md", ".html"})


def book_folder(library: Path, codex_id: str) -> Path | None:
    """The book's folder under the library: the first one named by its id."""
    if not CODEX.match(codex_id or "") or not Path(library).is_dir():
        return None
    hits = sorted(p for p in Path(library).iterdir() if p.is_dir() and p.name.startswith(codex_id))
    return hits[0] if hits else None


def book_relative(path: Path, codex_id: str) -> str | None:
    """The path as the book sees it (posix), or None when it is not under a
    folder named by the codex -- the only form an artefact path may take."""
    for parent in Path(path).parents:
        if parent.name.startswith(codex_id):
            return Path(path).relative_to(parent).as_posix()
    return None


def artefact_url(codex_id: str, rel: str) -> str:
    return f"/lib/{codex_id}/{PurePosixPath(rel).as_posix()}"


def resolve_artefact(library: Path, codex_id: str, rel: str) -> Path | None:
    """The file to serve, or None for anything that is not a listed artefact
    of this book: a codex that is not 14 digits, a path that resolves outside
    the folder, a suffix off the allowlist, a folder or a missing file."""
    folder = book_folder(library, codex_id)
    if folder is None or PurePosixPath(rel).suffix.lower() not in SUFFIXES:
        return None
    root = folder.resolve()
    target = (folder / rel).resolve()
    if target == root or not target.is_relative_to(root) or not target.is_file():
        return None
    return target
