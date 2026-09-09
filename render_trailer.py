"""Render every beat of the trailer's page, one H3 take each.

Run unattended: `uv run python render_trailer.py <codex_id>`.  Each take is
skipped when its file already exists, so a killed run resumes where it stopped
rather than paying for the takes it already has.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

from scripts.trailer import render_script as render

LIBRARY = Path("library")


def book_dir(codex_id: str) -> Path:
    found = sorted(LIBRARY.glob(f"{codex_id}*"))
    if not found:
        raise SystemExit(f"no book in library for {codex_id}")
    return found[0]


def render_all(book: Path) -> list[Path]:
    """Every beat rendered once, resuming over what is already on disk."""
    shots, refs = render.load(book)
    dest_dir = book / "trailer/main/clips/script"
    dest_dir.mkdir(parents=True, exist_ok=True)
    done, started = [], time.time()
    for i, shot in enumerate(shots, start=1):
        out = dest_dir / f"{shot['beat_id']}.mp4"
        if out.exists():
            print(f"[{i:2}/{len(shots)}] {shot['beat_id']} already rendered", flush=True)
            done.append(out)
            continue
        took = time.time()
        print(f"[{i:2}/{len(shots)}] {shot['beat_id']} {shot['seconds']:.1f}s "
              f"{shot.get('character') or 'no one'} @ {shot['place']} ...", flush=True)
        done.append(render.render_one(shot, refs, book, dest_dir))
        print(f"          done in {time.time() - took:.0f}s "
              f"({(time.time() - started) / 60:.0f} min elapsed)", flush=True)
    return done


if __name__ == "__main__":
    book = book_dir(sys.argv[1] if len(sys.argv) > 1 else "20260822113400")
    clips = render_all(book)
    print(f"=== RENDER done | {len(clips)} takes in {book / 'trailer/main/clips/script'} ===",
          flush=True)
