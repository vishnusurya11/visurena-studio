"""How much of each book's screenplay Wikiquote's editors already kept.

The number this prints is the one the slate depends on: with `kept < 2`
lines matched, the run is flying on text signals and says `iconicity: thin`
(research 7.3).  Read-only over `analysis/iconicity.json`; pass `--fetch` to
refresh the cache from Wikiquote first (network, one call per page revision).

Run: uv run python -m scripts.analysis.iconicity_coverage [--fetch] [codex_id ...]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from studio import iconicity, paths


def screenplay_lines(book_dir: Path) -> list[str]:
    """Every spoken line of the feature screenplay, in order."""
    path = book_dir / "screenplay/feature/screenplay.json"
    if not path.exists():
        return []
    doc = json.loads(path.read_text(encoding="utf-8"))
    return [e["text"] for sc in doc["scenes"] for e in sc.get("elements", [])
            if e.get("kind") == "dialogue" and e.get("text")]


def book_identity(book_dir: Path) -> tuple[str, str, tuple[str, ...]]:
    """Title, author, and the names the character-page hop may try."""
    book = json.loads((book_dir / "source/book.json").read_text(encoding="utf-8"))
    registry = json.loads((book_dir / "analysis/registry.json").read_text(encoding="utf-8"))
    names = tuple(c["name"] for c in registry.get("characters", [])
                  if c.get("role") in ("protagonist", "major"))
    return book["title"], book["author"], names


def coverage(book_dir: Path, kept: list[dict] | None = None) -> dict:
    """Lines of the screenplay that reproduce a kept quotation (Jaccard >= 0.8)."""
    kept = iconicity.load_cache(book_dir).get("kept", []) if kept is None else kept
    lines = screenplay_lines(book_dir)
    hits = [(line, hit) for line in lines if (hit := iconicity.match_kept(line, kept))]
    return {"book": book_dir.name, "lines": len(lines), "kept": len(kept),
            "matched": len(hits), "bold": sum(h["bold"] for _, h in hits),
            "examples": [line for line, _ in hits[:3]]}


def analysed_books(root: Path = paths.LIBRARY_ROOT) -> list[Path]:
    return sorted(p for p in Path(root).iterdir()
                  if (p / "screenplay/feature/screenplay.json").exists())


def main(argv: list[str]) -> None:
    fetch = "--fetch" in argv
    ids = [a for a in argv if not a.startswith("--")]
    books = [paths.book_dir(i) for i in ids] if ids else analysed_books()
    print(f"{'book':<48} {'lines':>5} {'kept':>5} {'match':>5} {'bold':>4}  status")
    for book in books:
        if fetch:
            title, author, names = book_identity(book)
            iconicity.fetch_wikiquote(title, author, names, book_dir=book)
        row = coverage(book)
        status = "full" if row["matched"] >= 2 else "thin"
        print(f"{row['book']:<48} {row['lines']:>5} {row['kept']:>5} {row['matched']:>5} "
              f"{row['bold']:>4}  {status}")


if __name__ == "__main__":
    main(sys.argv[1:])
