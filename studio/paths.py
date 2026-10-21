"""Path helpers — the codex id is the anchor; slugs are cosmetic and never assumed."""

from __future__ import annotations

from pathlib import Path

from studio import settings

LIBRARY_ROOT = settings.library_root(relative=True)
"""Today's cwd-relative `library`, or VISURENA_LIBRARY in a rehearsal (2026-10-21_ep02_proof 1.2)."""


def book_dir(codex_id: str, library_root: Path = LIBRARY_ROOT) -> Path:
    """The book's folder, found by id prefix (slug may change freely)."""
    matches = [p for p in Path(library_root).glob(f"{codex_id}_*") if p.is_dir()]
    if len(matches) != 1:
        raise FileNotFoundError(
            f"expected exactly 1 library folder for {codex_id}, found {len(matches)}"
        )
    return matches[0]
