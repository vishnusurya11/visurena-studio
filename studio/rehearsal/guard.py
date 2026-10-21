"""The stat guard: the SECOND check behind the fence (2026-10-21_ep02_proof 2.6, R7).

Before and after every rehearsal suite, a stat (size, mtime_ns) of the named real paths:
named folders are listed ONE level (ep01's sub-folders two), never walked (D: is a spinning
disk).  A directory's mtime moves when an entry is added or removed in it, so a new file two
levels under ep01 or anywhere in another book's top level or episodes/ shows; an overwrite
deeper than that does not, which is why the fence is the first check.  Any difference,
including a path that appears (ep02, a new db/*.db-* companion), fails the run with
`REAL LIBRARY TOUCHED: <path>`.  The fence refuses a write before it happens; this guard
catches whatever reached the disk some way the fence cannot see."""
from __future__ import annotations

import os
from pathlib import Path

from studio import settings

JEKYLL = "20260827135504_the-strange-case-of-dr-jekyll-and-mr-hyde"


class RealLibraryTouched(RuntimeError):
    """A real path changed between the guard's two snapshots."""


def listing(folder: Path) -> list[Path]:
    """A folder's direct entries (one level), [] when it is not a folder."""
    return sorted(folder.iterdir()) if folder.is_dir() else []


def subfolders(folder: Path) -> list[Path]:
    """A folder's direct sub-folders, from one directory read (scandir: no stat per entry)."""
    try:
        with os.scandir(folder) as entries:
            return sorted(Path(e.path) for e in entries if e.is_dir(follow_symlinks=False))
    except OSError:
        return []


def named_paths(repo: Path = settings.REPO, comfy: Path = settings.TODAY_COMFY_ROOT, book: str = JEKYLL) -> list[Path]:
    """The guarded paths of DESIGN 2.6: the book's top level, ep01's top level, its folders two
    deep and r2v takes, the absent ep02, every library entry and every book's episodes/ (so a
    write into another book shows), the VL log and cache, .autopilot, .device, every
    series.json, db/, the ComfyUI input/output folders and the two docs a rehearsal may only read."""
    lib, db = repo / settings.LIBRARY_DIR, repo / "db"
    home = lib / book
    ep01 = home / "episodes" / "ep01"
    deep = [sub for top in subfolders(ep01) for sub in subfolders(top)]
    named = [home, *listing(home), home / "episodes", home / "episodes" / "ep02", *listing(ep01), *deep,
             *listing(lib), *(b / "episodes" for b in subfolders(lib)),
             *listing(ep01 / "takes" / "r2v"), lib / "vlm_calls.jsonl", lib / ".vlm_cache",
             lib / ".autopilot", *listing(lib / ".autopilot"), lib / ".device", *listing(lib / ".device"),
             *sorted(lib.glob("*/autopilot/series.json")), db, db / "visurena_studio.db", *sorted(db.glob("*.db-*")),
             comfy / "input", comfy / "output", repo / "docs" / "DECISIONS.md", repo / "docs" / "episode_handbook.html"]
    return list(dict.fromkeys(named))


def entry_names(folder: Path) -> str:
    """A folder's direct entry names, sorted and joined (one directory read, no stat per entry)."""
    try:
        with os.scandir(folder) as entries:
            return "\n".join(sorted(e.name for e in entries))
    except OSError:
        return ""


def snapshot(paths: list[Path]) -> dict[str, tuple | None]:
    """path -> (size, mtime_ns), plus a folder's entry names; None for a path that does not exist.
    NTFS stamps a folder from a coarse clock, so an entry added in the snapshot's own tick leaves
    the folder's mtime unmoved: the names catch it."""
    out: dict[str, tuple | None] = {}
    for path in paths:
        try:
            st = os.stat(path)
        except OSError:
            out[str(path)] = None
            continue
        names = (entry_names(path),) if os.path.isdir(path) else ()
        out[str(path)] = (st.st_size, st.st_mtime_ns, *names)
    return out


def touched(before: dict, after: dict) -> list[str]:
    """One `REAL LIBRARY TOUCHED: <path>` line per path whose stat differs or appeared."""
    return [f"REAL LIBRARY TOUCHED: {p}" for p in sorted(set(before) | set(after)) if before.get(p) != after.get(p)]


def check(before: dict, paths: list[Path] | None = None) -> None:
    """Raise RealLibraryTouched unless a fresh snapshot equals `before`."""
    lines = touched(before, snapshot(named_paths() if paths is None else paths))
    if lines:
        raise RealLibraryTouched("\n".join(lines))
